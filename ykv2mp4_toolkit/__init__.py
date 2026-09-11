"""优酷 YKV → MP4 转换工具包。

模块：
    ykv_parser   - YKV 文件格式解析（提取 TS 分段 + DRM 字段）
    ykv_decrypt  - copyrightDRM 解密（密钥解包 + AES-ECB PES 解密）
    converter    - FFmpeg TS → MP4 合流
    main         - CLI 入口

快速使用：
    from ykv2mp4_toolkit.ykv_parser import YKVParser
    from ykv2mp4_toolkit.ykv_decrypt import setup_decryption, decrypt_ts_ecb
    from ykv2mp4_toolkit.converter import find_ffmpeg, ts_segments_to_mp4

    ykv = YKVParser().parse("ep1.ykv")
    key = setup_decryption(f"967436,{ykv.encryptR_server},{ykv.copyright_key}")
    segs = [decrypt_ts_ecb(s, key) for s in ykv.encrypted_segments]
    ts_segments_to_mp4(segs, "ep1.mp4", find_ffmpeg())
"""
__version__ = "1.0.0"
