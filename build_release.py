import os
import sys
import xmltodict
import subprocess
import zipfile
import plistlib
import re
import urllib.request
import urllib.parse
from pathlib import Path

PLIST_PATH = 'src/info.plist'
README_PATH = 'README.md'
ZIP_PATH = "./src" ### or "./"
ZIP_OUTPUT = "Alfred-Search-Obsidian-Notes-{version}.alfredworkflow"
exclude = {'.git', '__pycache__', '.DS_Store'}



# 1. 获取 info.plist 的 version 字段
def get_plist_version():

    with open(PLIST_PATH, 'rb') as f:
        plist_data = plistlib.load(f)

    version = plist_data.get('version')
    return version
# 2. 获取最新 git tag
def get_latest_tag():
    try:
        tag = subprocess.check_output(['git', 'tag', '--list', '--sort=-v:refname'], encoding='utf-8').split('\n')[0]
        return tag.strip() if tag else None
    except Exception:
        return None

# 3. 比较 version 和 tag
def should_release(version, tag):
    if not tag:
        return True
    # 只比较数字部分
    def norm(s):
        return [int(x) for x in s.strip('v').split('.') if x.isdigit()]
    return norm(version) > norm(tag)

# 4. 下载网络图片并替换链接
def download_images_and_replace_links(readme_content):
    # 匹配 Markdown 图片语法: ![alt](url)
    img_pattern = r'!\[([^\]]*)\]\((https?://[^\)]+)\)'
    matches = re.findall(img_pattern, readme_content)
    
    if not matches:
        return readme_content
    
    # 确保目标目录存在
    src_dir = Path(PLIST_PATH).parent
    images_dir = src_dir / 'images'
    images_dir.mkdir(exist_ok=True)
    
    modified_content = readme_content
    
    for alt_text, url in matches:
        try:
            print(f'正在下载图片: {url}')
            
            # 获取文件扩展名
            parsed_url = urllib.parse.urlparse(url)
            path_parts = Path(parsed_url.path).parts
            if path_parts:
                filename = path_parts[-1]
                # 如果文件名没有扩展名，尝试从 URL 参数或默认为 .png
                if '.' not in filename:
                    filename += '.png'
            else:
                filename = 'image.png'
            
            # 生成本地文件路径
            local_filename = f"image_{hash(url) % 100000}{Path(filename).suffix}"
            local_path = images_dir / local_filename
            
            # 下载图片
            with urllib.request.urlopen(url) as response:
                if response.status == 200:
                    with open(local_path, 'wb') as f:
                        f.write(response.read())
                    
                    # 替换 README 中的链接为相对路径
                    relative_path = f"images/{local_filename}"
                    old_link = f'![{alt_text}]({url})'
                    new_link = f'![{alt_text}]({relative_path})'
                    modified_content = modified_content.replace(old_link, new_link)
                    
                    print(f'图片下载成功: {local_filename}')
                else:
                    print(f'下载图片失败: {url} (状态码: {response.status})')
                    
        except Exception as e:
            print(f'下载图片时出错 {url}: {e}')
            continue
    
    return modified_content

# 5. 写入 readme 到 info.plist 的 readme 字段
def inject_readme():
    
    with open(PLIST_PATH, 'rb') as f:
        plist_data = plistlib.load(f)

    # 读取 README 内容
    readme_content = open(README_PATH, 'r', encoding='utf-8').read()
    
    # 下载图片并替换链接
    modified_readme = download_images_and_replace_links(readme_content)
    
    plist_data['readme'] = modified_readme

    with open(PLIST_PATH, 'wb') as f:
        plistlib.dump(plist_data, f)
        
# 6. 打包为 alfredworkflow 文件
def make_zip(version):
    name = ZIP_OUTPUT.format(version=version)
    with zipfile.ZipFile(name, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(ZIP_PATH):
            # 排除隐藏目录
            dirs[:] = [d for d in dirs if d not in exclude and not d.startswith('.')]
            for file in files:
                if file in exclude or file.endswith('.pyc') or file.startswith('.'):
                    continue
                path = os.path.join(root, file)
                # 使用相对于 ZIP_PATH 的路径，这样文件直接在 zip 根目录下
                arcname = os.path.relpath(path, ZIP_PATH)
                z.write(path, arcname)
    print(f'打包完成: {name}')
    return name

if __name__ == '__main__':
    version = get_plist_version()
    
    tag = get_latest_tag()
    print(f'info.plist version: {version}, latest tag: {tag}')
    if not should_release(version, tag):
        print('无需发布，version 未大于最新 tag')
        try:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write(f"skip=true\n")
        except Exception:
            pass
        sys.exit(0)
    
    inject_readme()
    zipname = make_zip(version)
    
    # 输出到 GitHub Actions
    try:
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f"workflow_file={zipname}\n")
            f.write(f"skip=false\n")
            f.write(f"version={version}\n")
    except Exception:
        pass
    
    print(f'生成的文件: {zipname}')
