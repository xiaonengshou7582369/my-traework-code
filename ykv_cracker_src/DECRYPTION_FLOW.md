# YKV 解密全链路

## 总览

```
.ykv 文件
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│ 1. 解析 (parser.rs)                                       │
│    • Mmap 打开文件                                         │
│    • 从尾部向前扫描 URL‑encoded JSON trailer               │
│    • JSON 反序列化 → segment 列表 [{name,offset,size},...] │
│    • 按 numeric name 排序 (1.ts, 2.ts … = PTS 顺序)       │
│    • 去除 34 字节 segment header (32 YK + 2 prefix)       │
│    • 提取 DRM 字段: encryptR_server, copyright_key        │
│    └→ Vec<Vec<u8>> encrypted_segments (N 段)              │
│                                                           │
├──────────────────────────────────────────────────────────┤
│ 2. 密钥解包 (key_unwrap.rs)                                │
│    Input: part1 + encryptR_server + copyright_key          │
│                                                           │
│    Layer 1:                                                │
│      key1 = hex(MD5(part1)[4:12])   // 16 ASCII 字节      │
│      data2 = base64_decode(encryptR_server)                │
│      R2 = AES-ECB-decrypt(key1, data2[:16])                │
│      r2_str = null_terminated(R2)                          │
│                                                           │
│    Layer 2:                                                │
│      key2 = hex(MD5(part1 || r2_str)[4:12])                │
│      data3 = base64_decode(copyright_key)                  │
│      raw = AES-ECB-decrypt(key2, data3)                    │
│    └→ 32 bytes raw key material                            │
│                                                           │
├──────────────────────────────────────────────────────────┤
│ 3. Custom Base64 (custom_b64.rs)                           │
│    Input: raw[:24] 字节                                    │
│    字母表: B-Z, a-z, 0-9, +, /  (排除 'A')               │
│    解码: 24 → 18 bytes                                    │
│    └→ 18 bytes key material                                │
│                                                           │
├──────────────────────────────────────────────────────────┤
│ 4. AES 密钥                                                │
│    取 key_material[:16] → 16 字节 AES-128 密钥             │
│    (DLL 中再做 aes_key_expand → 11 轮密钥,                 │
│     PyCrypto / RustCrypto 内部自动处理)                    │
│                                                           │
├──────────────────────────────────────────────────────────┤
│ 5. TS 解密 (decrypt.rs)                                    │
│    for each encrypted_segment:                              │
│      │                                                     │
│      ├─ 按 PES 分组 (PUSI=1 开始新 PES)                   │
│      │                                                     │
│      └─ for each PES group:                                │
│           ├─ 找出每包的 ES offset                           │
│           │  (跳过 TS header, adaptation field,             │
│           │   PES packet header)                            │
│           ├─ 收集 PES 内所有 ES chunk → 连续 buffer         │
│           ├─ AES-ECB 解密 floor(len/16) 个 block            │
│           └─ 解密结果 scatter 回各 TS packet                │
│    └→ Vec<Vec<u8>> decrypted_segments (N 段)               │
│                                                           │
├──────────────────────────────────────────────────────────┤
│ 6. PTS 修正 (output.rs)                                    │
│    • 扫描加密段首/尾 video PTS                              │
│    • 每段 duration = last_pts - first_pts                   │
│    • 累计偏移: seg[i] offset = sum(seg[0..i].duration)     │
│    • 写段前: new_pts = orig_pts + cumulative_offset         │
│                                                           │
├──────────────────────────────────────────────────────────┤
│ 7. 混流 MP4 (output.rs)                                    │
│    [主路径] pipe: decrypt → write → ffmpeg stdin            │
│    [降级]   写临时 TS 文件 → ffmpeg 转码                    │
│                                                           │
│    ffmpeg -f mpegts -i pipe:0 -c copy -movflags +faststart │
│    └→ output.mp4                                           │
└──────────────────────────────────────────────────────────┘
```

## DRM 数据来源

YKV JSON trailer 中提取:

| 字段              | JSON 路径                                                        | 用途               |
| ----------------- | ---------------------------------------------------------------- | ------------------ |
| `encryptR_server` | `dbInfo.info.configInfo.ups.data.data.stream[0].encryptR_server` | key_unwrap part2   |
| `copyright_key`   | 同上 `.stream_ext.copyright_key`                                 | key_unwrap part3   |
| `clientR1`        | `dbInfo.info.configInfo.R1Random`                                | (旧路径, 不再使用) |

`part1` 由用户提供 (6 位数字, 如 `967436`) 或 `--find-part1` 暴力枚举。

## 反汇编对照

| DLL 地址      | 函数名                  | 对应步骤                |
| ------------- | ----------------------- | ----------------------- |
| `0x18021B700` | ConfigContextDrm        | 入口, 组装 key_string   |
| `0x180256020` | key_unwrap              | 3 层 AES 解包           |
| `0x18064EDD0` | custom_b64_decode       | 24→18 base64            |
| `0x18064EBD0` | aes_key_expand          | AES 密钥扩展            |
| `0x18064F130` | tbEncryptionInit thread | PES-contiguous ECB 解密 |
| `0x18064F740` | tbEncryptionInit        | 每 AVPacket 解密        |

IDA DB: `D:\Program\YouKu\9.2.74.1001\nplayer64\aliplayerVS.dll.i64`

## AES-ECB 要点

- **ECB 模式**, 非 CBC (IDA 确认 `sub_64F740`)
- 作用在 **contiguous ES data** 上, 跨多个 TS 包
- 不是逐个 TS 包独立解密
- PyCrypto/RustCrypto ECB = DLL row-major (两个转置抵消)

## 分支矩阵

> 本文档只描述 **YK 文件 + drm_type=2 + 非 CMAF** 这条路径 (当前实现)。 \
> **完整的解密分支矩阵见 [RE/decrypt_paths_matrix.md](RE/decrypt_paths_matrix.md)** \
> 覆盖 YK/CMAF 双水源、drm_type {2,4,8,16,32}、CENC (AES-CTR/CBC) 与 Irdeto 各分支。

## 并发模型

| 层级       | 方式                              | 控制            |
| ---------- | --------------------------------- | --------------- |
| 文件间     | Rayon 线程池, 默认 2              | `-j` / `--jobs` |
| 段解密     | 后台线程超前 1 段 + 主线程写 pipe | 固定            |
| find_part1 | Rayon 全核并行 0–999999           | 固定            |

## 性能参考

| 场景          | Rust   | Python |
| ------------- | ------ | ------ |
| 单文件 236MB  | ~1.3s  | ~6.4s  |
| find_part1    | ~2s    | ~180s  |
| Batch 3 文件  | ~2.3s  | ~19s   |
| 内存 (单文件) | ~248MB | ~460MB |
