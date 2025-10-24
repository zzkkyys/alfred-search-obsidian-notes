# %%
# %load_ext autoreload
# %autoreload 2

# %%
import argparse
import json
import os
import time
from datetime import timedelta, datetime
import sys
from argparse import Namespace
from urllib.parse import quote
import requests
import sys
from base.alfred import Alfred, Alfred_Item
import hashlib
import asyncio
import aiohttp
import aiofiles
from content_processor import read_full_markdown_content





def cleanup_old_html_files():
    """Clean up HTML files older than 1 day"""
    try:
        current_time = time.time()
        one_day_ago = current_time - (24 * 60 * 60)  # 24 hours in seconds
        
        for filename in os.listdir(ALFRED_WORKFLOW_CACHE):
            if filename.endswith('.html'):
                filepath = os.path.join(ALFRED_WORKFLOW_CACHE, filename)
                # Skip default.html
                if filename == 'default.html':
                    continue
                    
                # Get file modification time
                file_mtime = os.path.getmtime(filepath)
                
                # Delete if older than 1 day
                if file_mtime < one_day_ago:
                    try:
                        os.remove(filepath)
                        print(f"Deleted old file: {filename}", file=sys.stderr)
                    except Exception as e:
                        print(f"Error deleting {filename}: {str(e)}", file=sys.stderr)
    except Exception as e:
        print(f"Error during cleanup: {str(e)}", file=sys.stderr)


def init_workflow():
    global ALFRED_WORKFLOW_CACHE, query_ports

    print("Python Version:", file=sys.stderr)
    print(sys.executable, file=sys.stderr)

    ALFRED_WORKFLOW_CACHE = os.environ["alfred_workflow_cache"]
    print(ALFRED_WORKFLOW_CACHE, file=sys.stderr)
    if not os.path.exists(ALFRED_WORKFLOW_CACHE):
        os.makedirs(ALFRED_WORKFLOW_CACHE, exist_ok=True)

    query_ports = os.environ["query_ports"]
    if ',' in query_ports:
        query_ports = query_ports.split(',')
        
    # Clean up old HTML files
    cleanup_old_html_files()
    
########################################################        
        

async def download_file(session, url, filepath):
    """Download a single file asynchronously"""
    try:
        async with session.get(url) as response:
            if response.status == 200:
                content = await response.read()
                async with aiofiles.open(filepath, 'wb') as f:
                    await f.write(content)
                return content.decode('utf-8')
            else:
                print(f"Error downloading {url}: HTTP {response.status}", file=sys.stderr)
                return None
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}", file=sys.stderr)
        return None
    
    
async def download_js_libraries():
    """Download or read cached JS libs; return dict of filename->code (empty string on failure)"""
    js_files = {
        'marked.min.js': {
            'url': 'https://cdn.jsdelivr.net/npm/marked@4.3.0/marked.min.js',
            'version': '4.3.0'
        },
        'tex-mml-chtml.js': {
            'url': 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js',
            'version': '3.2.2'
        },
        'mermaid.min.js': {
            'url': 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js',
            'version': '10.9.1'
        },
        # 新增：js-yaml（解析 frontmatter）
        'js-yaml.min.js': {
            'url': 'https://cdn.jsdelivr.net/npm/js-yaml@4.1.0/dist/js-yaml.min.js',
            'version': '4.1.0'
        }
    }
    js_cache_dir = os.path.join(ALFRED_WORKFLOW_CACHE, 'js')
    os.makedirs(js_cache_dir, exist_ok=True)

    version_file = os.path.join(js_cache_dir, 'versions.json')
    cached_versions = {}
    if os.path.exists(version_file):
        try:
            async with aiofiles.open(version_file, 'r', encoding='utf-8') as f:
                cached_versions = json.loads(await f.read() or '{}')
        except Exception:
            cached_versions = {}

    js_contents = {}
    async with aiohttp.ClientSession() as session:
        for filename, info in js_files.items():
            path = os.path.join(js_cache_dir, filename)
            need_update = (
                (filename not in cached_versions) or
                (cached_versions.get(filename) != info['version']) or
                (not os.path.exists(path))
            )
            if need_update:
                try:
                    code = await download_file(session, info['url'], path)
                    if code is None:
                        # 网络失败，尝试读本地旧缓存
                        try:
                            async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                                code = await f.read()
                        except Exception:
                            code = ''
                    js_contents[filename] = code
                    cached_versions[filename] = info['version']
                except Exception:
                    js_contents[filename] = ''
            else:
                try:
                    async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                        js_contents[filename] = await f.read()
                except Exception:
                    js_contents[filename] = ''

    try:
        async with aiofiles.open(version_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(cached_versions))
    except Exception:
        pass

    return js_contents



async def generate_html_async(content: str, search_terms=None, page_width: str = None) -> str:
    js_contents = await download_js_libraries()

    template_path = os.path.join(os.path.dirname(__file__), 'template.html')
    if not hasattr(generate_html_async, 'template_cache'):
        async with aiofiles.open(template_path, 'r', encoding='utf-8') as f:
            generate_html_async.template_cache = await f.read()
    tpl = generate_html_async.template_cache

    # 注入脚本源码
    html = (tpl
        .replace('{marked_js}', js_contents.get('marked.min.js',''))
        .replace('{mathjax_js}', js_contents.get('tex-mml-chtml.js',''))
        .replace('{mermaid_js}', js_contents.get('mermaid.min.js',''))
        .replace('{jsyaml_js}', js_contents.get('js-yaml.min.js',''))  # 若有 frontmatter 解析
    )

    # 注入搜索词 JSON（空数组也要是 '[]'）
    terms_json = json.dumps(search_terms or [], ensure_ascii=False)
    html = html.replace('{search_terms_json}', terms_json)

    #（可选）替换 max width 变量
    if page_width:
        html = html.replace('--page-width: 860px', f'--page-width: {page_width}')

    # 注入 Markdown 原文
    marker = '<script type="text/markdown" id="md-src"></script>'
    html = html.replace(marker, f'<script type="text/markdown" id="md-src">{content}</script>')

    # 落地缓存
    hash_value = hashlib.sha256(html.encode('utf-8')).hexdigest()
    html_path = os.path.join(ALFRED_WORKFLOW_CACHE, f"{hash_value}.html")
    if not os.path.exists(html_path):
        async with aiofiles.open(html_path, "w", encoding='utf-8') as f:
            await f.write(html)
    return html_path


def generate_html(content, search_terms=None, page_width: str = None) -> str:
    """Synchronous wrapper for generate_html_async"""
    return asyncio.run(generate_html_async(content, search_terms=search_terms, page_width=page_width))


def get_obsidian_URI_from_query_res(query_res:list):
    obsidian_url = "obsidian://advanced-uri?vault={}&filepath={}"
    # obsidian_url = "obsidian://advanced-uri?vault={}"
    for res in query_res:
        res['URI'] = obsidian_url.format(quote(res['vault']), quote(res['path']))   
        res['arg'] = f"{res['vault']}|||||{res['path']}"
        # 使用新的内容处理器
        # res = process_search_result(res, ALFRED_WORKFLOW_CACHE, generate_html)
        full_content = read_full_markdown_content(res['vault'], res['path'])
        # res["quicklookurl"] = generate_html(full_content)
        # 关键：把 foundWords 注入，自动高亮 + 滚动到第一个
        search_terms = res.get('foundWords', [])
        res["quicklookurl"] = generate_html(full_content, search_terms=search_terms)



# %%
def query_multiple_vault(query, query_ports):
    res = []
    if not isinstance(query_ports, list):
        query_ports = [query_ports]
        
    for port in query_ports:
        try:
            url = f"http://localhost:{port}/search?q={query}"
            response = requests.get(url)
            data = eval(response.text)
            res += data
        except Exception as e:
            print(e, file=sys.stderr)
            continue
    get_obsidian_URI_from_query_res(res)
    return res


# %%

# %% tags=[]
def main(args):
    data = query_multiple_vault(args.query, query_ports)
    
    items = []
    for _d in data:
        _d = Namespace(**_d)
        _item = Alfred_Item(
            title=_d.basename,
            subtitle=_d.excerpt,
            # arg=_d.URI,
            arg=_d.arg,
            quicklookurl=_d.quicklookurl,
        )
        items.append(_item)

    alfred = Alfred(items)
    alfred.output_items()


# %% tags=[]
if __name__ == "__main__":
    
    ### get alfred workflow cache and obsidian query ports
    init_workflow()
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str)
    args = parser.parse_args()
    main(args)

