import sys, os, subprocess, tempfile
sys.path.insert(0, r'c:\Users\Administrator\iCloudDrive\Traework云仓库\6aa2615da516df5d0a1843ba')
from ykv2mp4_toolkit.ykv_parser import YKVParser
from ykv2mp4_toolkit.ykv_decrypt import setup_decryption, decrypt_ts_ecb

ykv = YKVParser().parse(r'D:\Youku Files\download\沧元图\第2集 今晚来点狠的-国语.ykv')
ks = f'288466,{ykv.encryptR_server},{ykv.copyright_key}'
key = setup_decryption(ks)
print('AES key:', key.hex())

seg0 = decrypt_ts_ecb(ykv.encrypted_segments[0], key)
print('seg0 first 16B:', seg0[:16].hex())
print('seg0[0]=0x{:02x} (expect 0x47)'.format(seg0[0]))

# Try ffmpeg on first 3 segments
td = tempfile.mkdtemp(prefix='ykv_dbg_')
print('tempdir:', td)

for i in range(3):
    seg = decrypt_ts_ecb(ykv.encrypted_segments[i], key)
    p = os.path.join(td, str(i) + '.ts')
    with open(p, 'wb') as f:
        f.write(seg)
    print(f'  seg{i}: first byte=0x{seg[0]:02x}, size={len(seg)}')

cf = os.path.join(td, 'c.txt')
with open(cf, 'w', encoding='utf-8') as f:
    for i in range(3):
        p = os.path.join(td, str(i) + '.ts')
        escaped = p.replace("'", "'\\''")
        f.write(f"file '{escaped}'\n")
print('concat file:', open(cf).read())

ff = r'c:\Users\Administrator\iCloudDrive\Traework云仓库\6aa2615da516df5d0a1843ba\refs\ykv转mp4+8.1\ykv转mp4 8.1\ffmpeg\ffmpeg.exe'
out = os.path.join(td, 'out.mp4')
r = subprocess.run([ff, '-y', '-f', 'concat', '-safe', '0', '-i', cf, '-c', 'copy', out],
                   capture_output=True)
print('exit:', r.returncode)
print('STDERR tail:', r.stderr.decode('utf-8', 'replace')[-2000:] if r.stderr else '(none)')
print('output exists:', os.path.exists(out), 'size:', os.path.getsize(out) if os.path.exists(out) else 0)
