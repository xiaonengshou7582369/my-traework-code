# ykv-cracker

优酷 YKV 视频文件解密与转换工具。纯 Rust + Python 双实现，基于 IDA Pro 逆向 `aliplayerVS.dll` 的 DRM 解密管线，无需 DLL 注入。

## 特性

- **完整 DRM 管线** — key_unwrap → custom base64 → AES-ECB，逐字节匹配 DLL
- **直接输出 MP4** — 解密后 stream copy 转 MP4，不重编码
- **自动穷举 part1** — 无需抓包，`--find-part1` ~2 秒自动找到密钥
- **批量处理** — 多文件并行转换，`-j` 可调并发（默认 2）
- **流式解密** — 边解密边 pipe 给 ffmpeg，单文件峰值内存仅 ~245MB
- **双实现** — Rust（高性能）+ Python（可读性），同一代码库

## 解密流程

### YKV 文件格式

```
┌─ JPEG 封面图 ─────────────────────────────┐
├─ YK 段头(32B) + 2B 前缀 + 加密 TS 数据 ① ─┤
├─ YK 段头(32B) + 2B 前缀 + 加密 TS 数据 ② ─┤
├─ ... ──────────────────────────────────────┤
├─ URL 编码的 JSON 尾（段索引 + DRM 密钥）─────┤
└─ 16 字节 JSON 大小 ────────────────────────┘
```

JSON 尾是一个数组，包含 `{name, offset, size}` 段索引和 `dbInfo` DRM 元数据。

### DRM 密钥管线

```
key_string = "part1,encryptR_server,copyright_key"
  │
  ▼ 第 1 层：K1 = MD5(part1)[4:12].hex → AES-ECB 解密 part2 → R2
  ▼ 第 2 层：K2 = MD5(part1 || R2)[4:12].hex → AES-ECB 解密 part3 → key_material
  ▼ custom_b64_decode(key_material[:24]) → 18 字节（字母表排除 'A'）
  ▼ 取前 16 字节作为 AES-128 密钥
  ▼ AES-ECB 解密 PES 连续 ES 数据（跨越 TS 包边界）
  ▼ 解密后的 H.264 + AAC → ffmpeg remux → MP4
```

**解密细节：**

- 解密在 **PES 层** 操作。AES-ECB 的 16 字节块边界**跨越 TS 包**，必须将同一 PES 内的所有 TS 包连起来整体解密，再写回各包。
- TS 头、adaptation field、PSI 表（PAT/PMT/SDT）和 PES 头都保持明文，只加密 ES 数据。
- 段按 **数字文件名**（1.ts, 2.ts …）排序 = PTS 顺序。
- 段头剥离：每段数据从 `offset+34`（32 字节 YK 头 + 2 字节前缀）读取，尺寸取 JSON 的 `size`。

完整的 7 步全链路说明见 [DECRYPTION_FLOW.md](DECRYPTION_FLOW.md)。

### part1 的获取

`part1` 是 6 位数字，不在 YKV 文件中。三种方式获得：

1. **已知时直接指定**：`--part1 967436`
2. **自动穷举**：`--find-part1`（~2 秒，8 核并行 MD5 + AES）
3. **完整密钥串**：`--key-string "a,b,c"`

穷举原理：错误 part1 解出的 R2 是随机字节，同时是 `0-9a-f` 的概率仅 ~10⁻¹⁷，百万次穷举假阳性期望 ~0。

## 安装

### Rust 版（推荐，高性能）

```bash
cargo build --release
# 二进制在 target/release/ykv-cracker.exe
```

### Python 版

```bash
uv sync          # 安装依赖（开发模式，含 pytest）
uv run ykv-cracker --help
```

### 依赖

- **ffmpeg** — 用于 TS→MP4 remux，需在 PATH 或 `--ffmpeg` 指定

## 使用

### 单文件转换

```bash
# Rust
target/release/ykv-cracker "影片.ykv" --part1 967436 -o 影片.mp4

# Python
uv run ykv-cracker "影片.ykv" --part1 967436 -o 影片.mp4
```

### 自动穷举 part1

```bash
target/release/ykv-cracker "影片.ykv" --find-part1 -o 影片.mp4
```

### 批量处理

```bash
# 多个文件
target/release/ykv-cracker "ep01.ykv" "ep02.ykv" "ep03.ykv" --part1 967436

# 整个目录（自动扫描 .ykv）
target/release/ykv-cracker "E:\视频" --part1 967436
```

批量模式下默认 **2 个文件并行**（平衡内存与吞吐），可用 `-j` 调整：

```bash
target/release/ykv-cracker "E:\视频" --part1 967436 -j 1   # 串行，最低内存
target/release/ykv-cracker "E:\视频" --part1 967436 -j 4   # 4 并发
target/release/ykv-cracker "E:\视频" --part1 967436 -j 0   # 全核跑满
```

### 完整密钥串

```bash
target/release/ykv-cracker "影片.ykv" \
  --key-string "967436,JhEDEbgYP7/QnQm+ffozQw==,imKpn7LT6fT+c8ucn77K9FUVW4hJG7pSyDq1Xn7k0KY="
```

### 保留中间 TS

```bash
target/release/ykv-cracker "影片.ykv" --part1 967436 -o 影片.mp4 --keep-ts
```

注意：`--keep-ts` 需要把所有解密段存内存写 TS 文件，峰值内存约 ~462MB，非流式路径。

## 性能

| 测试                      | Rust       | Python | 加速比   |
| ------------------------- | ---------- | ------ | -------- |
| 单文件解密+转MP4          | **1.3s**   | 6.4s   | **4.9×** |
| `--find-part1`（100万次） | **2s**     | 180s   | **90×**  |
| 批量 3 文件（并行）       | **2.3s**   | 19s    | **8.3×** |
| 峰值内存（流式）          | **~245MB** | ~460MB | **1.9×** |

## 项目结构

```
ykv-cracker/
├── src/                    # Rust 实现
│   ├── main.rs             # 入口，批处理调度（rayon 并行）
│   ├── cli.rs              # CLI 参数（clap）
│   ├── parser.rs           # YKV 解析（mmap + serde_json）
│   ├── key_unwrap.rs       # 3 层密钥解包 + 并行穷举 part1
│   ├── custom_b64.rs       # 自定义 base64 解码（字母表排除 'A'）
│   ├── decrypt.rs          # PES 连续 AES-ECB 解密
│   ├── output.rs           # 流式 pipe + PTS 修正 + ffmpeg remux
│   ├── error.rs            # 错误类型
│   └── types.rs            # 共享类型
├── ykv_cracker/            # Python 实现（功能等价）
│   ├── cli.py              # CLI 入口
│   ├── parser.py           # YKV 解析
│   ├── key_unwrap.py       # 密钥解包
│   ├── custom_b64.py       # 自定义 base64
│   ├── aes_core.py         # AES 密钥扩展
│   ├── config_drm.py       # ConfigContextDrm 入口
│   ├── decryptor.py        # TS 解密
│   └── converter.py        # ffmpeg 包装
├── tests/                  # Python 测试（52 个）
├── RE/                     # IDA 逆向分析文档
├── json/                   # JSON 尾样本（调试用）
├── DECRYPTION_FLOW.md      # 解密全链路说明
├── Cargo.toml
├── pyproject.toml
└── uv.lock
```

## 常见问题

### Q: 怎么知道 part1？

用 `--find-part1` 自动穷举，或从播放器网络请求中获得。

### Q: 支持哪些编码？

视频：H.264，音频：AAC。未测试其他编码格式。

### Q: 支持哪些ykv文件？

当前测试面向 `drm_type=2` 的 YKV 文件（可能为优酷会员独播），其他类型未测试。

## 免责声明

本项目由 DeepSeek V4 逆向分析 `aliplayerVS.dll` 得到的 DRM 解密管线实现，**仅用于学习和研究**。请勿用于非法下载或传播受版权保护的内容。

## License

[GPL-3.0](LICENSE) — GNU General Public License v3
