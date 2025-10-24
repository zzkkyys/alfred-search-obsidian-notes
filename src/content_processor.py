"""
Obsidian Content Processor
处理 Obsidian 文件内容的获取、高亮和HTML生成
"""

import os
import sys
import json
import re
import hashlib
from pathlib import Path


def get_vault_path(vault_name):
    """尝试获取 vault 的完整路径"""
    # 首先尝试从 Obsidian 配置中查找
    obsidian_config_path = os.path.expanduser("~/Library/Application Support/obsidian/obsidian.json")
    try:
        if os.path.exists(obsidian_config_path):
            with open(obsidian_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                vaults = config.get('vaults', {})
                for vault_id, vault_info in vaults.items():
                    if vault_info.get('path') and vault_name in vault_info.get('path', ''):
                        vault_path = vault_info['path']
                        if os.path.exists(vault_path):
                            return vault_path
    except Exception as e:
        print(f"Error reading Obsidian config: {e}", file=sys.stderr)
    
    # 备用方案：搜索常见位置
    possible_paths = [
        os.path.expanduser("~/Documents"),
        os.path.expanduser("~/Desktop"),
        os.path.expanduser("~/Downloads"),
        os.path.expanduser("~/"),
        os.path.expanduser("~/Library/Mobile Documents/iCloud~md~obsidian/Documents"),  # iCloud
    ]
    
    for base_path in possible_paths:
        if not os.path.exists(base_path):
            continue
            
        # 精确匹配
        vault_path = os.path.join(base_path, vault_name)
        if os.path.exists(vault_path) and os.path.isdir(vault_path):
            return vault_path
        
        # 搜索子目录
        try:
            for item in os.listdir(base_path):
                item_path = os.path.join(base_path, item)
                if os.path.isdir(item_path) and vault_name in item:
                    # 检查是否包含 .obsidian 目录，确认这是一个 vault
                    if os.path.exists(os.path.join(item_path, '.obsidian')):
                        return item_path
        except PermissionError:
            continue
    
    # 如果没找到，返回None
    return None


def read_full_markdown_content(vault_name, file_path):
    """读取 markdown 文件的完整内容"""
    try:
        # 获取 vault 完整路径
        vault_path = get_vault_path(vault_name)
        if not vault_path:
            print(f"Cannot find vault: {vault_name}", file=sys.stderr)
            return None
        
        # 构建完整文件路径
        full_file_path = os.path.join(vault_path, file_path)
        
        if not os.path.exists(full_file_path):
            print(f"File not found: {full_file_path}", file=sys.stderr)
            return None
            
        # 读取文件内容
        with open(full_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return content
        
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}", file=sys.stderr)
        return None
