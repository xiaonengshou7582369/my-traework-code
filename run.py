"""ykv2mp4 顶层入口（PyInstaller 打包用）。

打包：
    python build_exe.py

运行（打包后或源码模式）：
    python run.py "D:\\file.ykv" --find-part1
"""
import sys
import os

# 源码模式下确保 workspace 根目录在 sys.path
if not getattr(sys, "frozen", False):
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)

from ykv2mp4_toolkit.main import main

if __name__ == "__main__":
    sys.exit(main())
