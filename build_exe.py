#!/usr/bin/env python3
"""
PyInstaller打包脚本
生成Windows可执行文件
"""

import PyInstaller.__main__
import os
import shutil

def clean_build():
    """清理之前的构建文件"""
    dirs_to_remove = ['build', 'dist']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"已删除: {dir_name}")

def build_exe():
    """执行打包"""
    
    # 清理之前的构建
    clean_build()
    
    # PyInstaller参数
    args = [
        '主程序.py',                          # 主程序入口
        '--name=游戏手柄触屏映射工具',          # 应用名称
        '--onefile',                          # 打包为单文件
        '--windowed',                         # Windows应用（无控制台窗口）
        '--clean',                            # 清理临时文件
        '--noconfirm',                        # 不确认覆盖
        
        # 添加数据文件
        '--add-data=虚拟键盘网格布局.py;.',
        
        # 隐藏导入
        '--hidden-import=inputs',
        '--hidden-import=PIL',
        '--hidden-import=pystray',
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.ttk',
        '--hidden-import=tkinter.messagebox',
        
        # 排除不必要的模块以减小体积
        '--exclude-module=matplotlib',
        '--exclude-module=numpy',
        '--exclude-module=pandas',
        '--exclude-module=scipy',
        '--exclude-module=pytest',
        '--exclude-module=unittest',
        '--exclude-module=pydoc',
        '--exclude-module=email',
        '--exclude-module=http',
        '--exclude-module=xml',
        '--exclude-module=xmlrpc',
        '--exclude-module=html',
        '--exclude-module=lib2to3',
        '--exclude-module=distutils',
        '--exclude-module=multiprocessing',
        '--exclude-module=concurrent',
        '--exclude-module=asyncio',
        '--exclude-module=unittest',
        '--exclude-module=test',
        '--exclude-module=tkinter.test',
        '--exclude-module=sqlite3',
        '--exclude-module=pdb',
        '--exclude-module=doctest',
        '--exclude-module=ctypes.test',
        '--exclude-module=_tkinter',
        
        # 优化
        '--strip',                            # 去除符号表
    ]
    
    print("开始打包...")
    print(f"参数: {' '.join(args)}")
    
    PyInstaller.__main__.run(args)
    
    print("\n打包完成!")
    print(f"可执行文件位置: dist/游戏手柄触屏映射工具.exe")

def create_release_package():
    """创建发行版包"""
    import zipfile
    from datetime import datetime
    
    exe_name = '游戏手柄触屏映射工具.exe'
    exe_path = os.path.join('dist', exe_name)
    
    if not os.path.exists(exe_path):
        print(f"错误: 找不到 {exe_path}")
        return
    
    # 创建发行目录
    release_dir = '发行版'
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    os.makedirs(release_dir)
    
    # 复制exe文件
    shutil.copy(exe_path, os.path.join(release_dir, exe_name))
    
    # 复制说明文档
    for doc in ['README.md', 'DEVELOPMENT.md']:
        if os.path.exists(doc):
            shutil.copy(doc, release_dir)
    
    # 创建zip包
    version = datetime.now().strftime('%Y%m%d')
    zip_name = f'游戏手柄触屏映射工具_v{version}.zip'
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(release_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, release_dir)
                zipf.write(file_path, arcname)
    
    print(f"\n发行版已创建: {zip_name}")
    print(f"包含文件:")
    for f in os.listdir(release_dir):
        print(f"  - {f}")

if __name__ == "__main__":
    build_exe()
    create_release_package()
