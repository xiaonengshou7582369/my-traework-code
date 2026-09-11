"""Fetch all comments from B站 videos and parse them."""
import json
import urllib.request
import urllib.parse
import time
import re
from pathlib import Path

OUT = Path(r"c:\Users\Administrator\iCloudDrive\Traework云仓库\6aa2615da516df5d0a1843ba\comments")
OUT.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
    "Accept": "application/json",
}

def fetch_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read().decode("utf-8", errors="replace")
            # Remove control chars
            data = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", data)
            return json.loads(data)
    except Exception as e:
        print(f"  Error fetching {url[:100]}: {e}")
        return None

def get_aid(bvid):
    """Get aid from BV id."""
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    data = fetch_json(url)
    if data and data.get("code") == 0:
        aid = data["data"]["aid"]
        title = data["data"]["title"]
        reply_count = data["data"]["stat"]["reply"]
        print(f"  {bvid}: aid={aid}, title={title}, replies={reply_count}")
        return aid, title, reply_count
    return None, None, 0

def fetch_comments(aid, max_pages=15):
    """Fetch all comments using old reply API (sort=2 = by likes)."""
    all_comments = []
    for pn in range(1, max_pages + 1):
        url = f"https://api.bilibili.com/x/v2/reply?type=1&oid={aid}&pn={pn}&ps=20&sort=2"
        data = fetch_json(url)
        if not data or data.get("code") != 0:
            print(f"    Page {pn}: error or no data")
            break
        replies = data.get("data", {}).get("replies", [])
        if not replies:
            print(f"    Page {pn}: no more replies")
            break
        for r in replies:
            msg = r.get("content", {}).get("message", "")
            name = r.get("member", {}).get("uname", "")
            likes = r.get("like", 0)
            all_comments.append({"name": name, "msg": msg, "likes": likes, "sub": []})
            # Sub-replies
            for s in (r.get("replies") or [])[:3]:
                smsg = s.get("content", {}).get("message", "")
                sname = s.get("member", {}).get("uname", "")
                all_comments[-1]["sub"].append({"name": sname, "msg": smsg})
        print(f"    Page {pn}: {len(replies)} replies")
        time.sleep(0.5)
    return all_comments

videos = [
    ("BV1uWhfenEAe", "video1_全网最简单"),
    ("BV1QBNjzFEyR", "video2_快速转mp4_vbs"),
    ("BV1Gt3nevEQp", "video3_全网首发_源码"),
]

for bvid, label in videos:
    print(f"\n=== {label} ({bvid}) ===")
    aid, title, reply_count = get_aid(bvid)
    if not aid:
        print("  Failed to get aid")
        continue
    comments = fetch_comments(aid)
    # Save to file
    out_file = OUT / f"{label}_{bvid}.txt"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(f"Video: {title}\nBV: {bvid}  aid: {aid}  total replies: {reply_count}\n")
        f.write(f"Fetched: {len(comments)} comments\n")
        f.write("=" * 70 + "\n\n")
        for c in comments:
            f.write(f"[{c['likes']}赞] {c['name']}: {c['msg']}\n")
            for s in c["sub"]:
                f.write(f"  L {s['name']}: {s['msg']}\n")
    print(f"  Saved {len(comments)} comments to {out_file.name}")

# Print all comments for analysis
print("\n\n" + "=" * 70)
print("ALL COMMENTS FOR ANALYSIS")
print("=" * 70)
for bvid, label in videos:
    out_file = OUT / f"{label}_{bvid}.txt"
    if out_file.exists():
        print(f"\n--- {label} ({bvid}) ---")
        with open(out_file, "r", encoding="utf-8") as f:
            print(f.read())
