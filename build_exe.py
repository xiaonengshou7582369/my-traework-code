"""打包 ykv2mp4_toolkit 为单个 ykv2mp4.exe。

打包后：
- ykv2mp4.exe  (含 Python 解释器 + pycryptodome + 所有代码)
- ffmpeg.exe   (从 refs/ 复制)
- 使用说明.txt

目标电脑零依赖，下载即用。
"""
import os
import shutil
import subprocess
import sys

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
TOOLKIT_DIR = os.path.join(WORKSPACE, "ykv2mp4_toolkit")
DIST_DIR = os.path.join(WORKSPACE, "dist")
BUILD_DIR = os.path.join(WORKSPACE, "build")

# refs 中两个 ffmpeg 源
FFMPEG_SOURCES = [
    os.path.join(WORKSPACE, "refs", "ykv转mp4+8.1", "ykv转mp4 8.1", "ffmpeg", "ffmpeg.exe"),
    os.path.join(WORKSPACE, "refs", "ykv2mp4", "ykv2mp4", "ffmpeg", "ffmpeg.exe"),
]

ENTRY = os.path.join(WORKSPACE, "run.py")


def find_ffmpeg() -> str | None:
    for p in FFMPEG_SOURCES:
        if os.path.exists(p):
            return p
    return None


def main():
    print("=== ykv2mp4.exe 打包脚本 ===\n")

    # 1. 检查 ffmpeg
    ffmpeg_src = find_ffmpeg()
    if not ffmpeg_src:
        print("错误: 未找到 ffmpeg.exe，请确保 refs/ 目录存在")
        return 1
    print(f"ffmpeg 源: {ffmpeg_src}")
    print(f"  大小: {os.path.getsize(ffmpeg_src)/1024/1024:.1f} MB")

    # 2. 清理旧的 build/dist
    for d in (BUILD_DIR, DIST_DIR):
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)
    os.makedirs(DIST_DIR, exist_ok=True)

    # 3. PyInstaller 打包
    # --onefile: 单个 exe
    # --name: 输出名 ykv2mp4.exe
    # --add-data: 捆绑 ffmpeg.exe 到 exe 内的 ffmpeg/ 子目录
    # --hidden-import: 确保 Crypto 子模块全部打入
    ffmpeg_data = f"{ffmpeg_src}{os.pathsep}ffmpeg"
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "ykv2mp4",
        "--add-data", ffmpeg_data,
        "--hidden-import", "Crypto.Cipher.AES",
        "--hidden-import", "Crypto.Cipher.DES",
        "--hidden-import", "Crypto.Util.Padding",
        "--hidden-import", "Crypto.Util.strxor",
        "--hidden-import", "Crypto.Util.Counter",
        "--clean",
        "--noconfirm",
        "--workpath", BUILD_DIR,
        "--distpath", DIST_DIR,
        ENTRY,
    ]
    print(f"\n执行: {' '.join(cmd[:6])}...\n")
    r = subprocess.run(cmd, cwd=WORKSPACE)
    if r.returncode != 0:
        print("打包失败!")
        return r.returncode

    exe_path = os.path.join(DIST_DIR, "ykv2mp4.exe")
    if not os.path.exists(exe_path):
        print(f"错误: 未生成 {exe_path}")
        return 1

    size_mb = os.path.getsize(exe_path) / 1024 / 1024
    print(f"\n打包成功!")
    print(f"  路径: {exe_path}")
    print(f"  大小: {size_mb:.1f} MB")

    # 4. 在 dist 旁放一份 ffmpeg.exe 和使用说明（便于用户直接看到）
    ffmpeg_dst = os.path.join(DIST_DIR, "ffmpeg.exe")
    if not os.path.exists(ffmpeg_dst):
        shutil.copy2(ffmpeg_src, ffmpeg_dst)
    print(f"  ffmpeg: {ffmpeg_dst}")

    # 5. 写使用说明
    readme = os.path.join(DIST_DIR, "使用说明.txt")
    with open(readme, "w", encoding="utf-8") as f:
        f.write("""ykv2mp4 优酷 YKV 转 MP4 工具
===============================

【用法 1】单文件转换（自动暴力枚举解密密钥）
    ykv2mp4.exe "D:\\路径\\第1集.ykv" --find-part1

    输出 MP4 会和源文件在同一目录。

【用法 2】单文件 + 指定输出
    ykv2mp4.exe "D:\\第1集.ykv" --find-part1 -o "D:\\out\\第1集.mp4"

【用法 3】批量处理整个目录
    ykv2mp4.exe "D:\\Youku Files\\download\\沧元图" -b --find-part1 -O "D:\\out"

    -b         批量模式
    --find-part1 每集自动枚举解密密钥（约2秒/集）
    -O         输出目录

【用法 4】已知 part1 时跳过枚举（更快）
    ykv2mp4.exe "D:\\第1集.ykv" --part1 288466

【参数说明】
    --find-part1   暴力枚举6位 part1（推荐，每集不同）
    --part1 N      直接指定 part1（6位数字）
    --key-string   完整密钥串 "part1,encR,ckey"
    -b             批量处理目录下所有 .ykv
    -o PATH        输出 MP4 路径（单文件）
    -O PATH        输出目录（批量模式）
    --keep-ts      保留中间 TS 文件
    --ffmpeg PATH  指定 ffmpeg 路径（默认用内置）

【零依赖】
本工具包已内置 Python 运行时 + pycryptodome + ffmpeg，
目标电脑无需安装任何软件，下载即用。

【输出格式】
1080p HEVC + AAC，MP4 容器，兼容主流播放器。
""")
    print(f"  说明: {readme}")
    print(f"\n完成! 工具包在: {DIST_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
