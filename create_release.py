#!/usr/bin/env python3
"""
创建发行版包
"""

import os
import shutil
import zipfile
from datetime import datetime

def create_release():
    exe_name = '游戏手柄触屏映射工具.exe'
    exe_path = os.path.join('dist', exe_name)
    
    if not os.path.exists(exe_path):
        print(f"错误: 找不到 {exe_path}")
        return
    
    release_dir = '发行版'
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    os.makedirs(release_dir)
    
    shutil.copy(exe_path, os.path.join(release_dir, exe_name))
    
    for doc in ['README.md', 'DEVELOPMENT.md']:
        if os.path.exists(doc):
            shutil.copy(doc, release_dir)
    
    version = datetime.now().strftime('%Y%m%d')
    zip_name = f'游戏手柄触屏映射工具_v{version}.zip'
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(release_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, release_dir)
                zipf.write(file_path, arcname)
    
    print(f"发行版已创建: {zip_name}")
    print(f"包含文件:")
    for f in os.listdir(release_dir):
        print(f"  - {f}")
    
    file_size = os.path.getsize(zip_name) / (1024 * 1024)
    print(f"\n文件大小: {file_size:.2f} MB")

if __name__ == "__main__":
    create_release()
