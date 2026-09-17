#!/usr/bin/env python3
import json, re, subprocess, html, time, os, sys
from urllib.parse import urljoin

manifest_path = "Z:/AnderZilla-docs/editorial/launch-2026-09-10/launch-manifest.json"
out_path = "Z:/AnderZilla-docs/editorial/launch-2026-09-10/real-media-2026-09-16/research_prelim.json"

with open(manifest_path, encoding="utf-8") as f:
    data=json.load(f)
items=data["items"]

def curl_get_body(url):
    try:
        r=subprocess.run(["curl","-sL","-A","Mozilla/5.0 (Windows NT 10.0; Win64; x64) AnderZillaResearch/1.0","--max-time","20","--compressed",url], capture_output=True, timeout=25)
        return r.stdout.decode("utf-8", errors="ignore"), r.returncode
    except Exception as e:
        return f"ERROR: {e}", 1

def verify_url(url):
    try:
        r=subprocess.run(["curl","-sL","-o","NUL","-w","%{http_code}:%{content_type}","-A","Mozilla/5.0 AnderZillaResearch/1.0","--max-time","15",url], capture_output=True, text=True, timeout=20)
        out=r.stdout.strip()
        if ":" in out:
            code, ctype = out.split(":",1)
        else:
            code, ctype = out, ""
        ok = code=="200" and ("image" in ctype or code=="200")
        return {"code":code, "ctype":ctype, "ok": ok}
    except Exception as e:
        return {"code":"ERR", "ctype":str(e), "ok":False}

def extract_images(body, base_url):
    metas=[]
    for m in re.finditer(r'<meta[^>]+property=["\']og:image["\'][^>]*>', body, re.I):
        tag=m.group(0)
        cm=re.search(r'content=["\']([^"\']+)["\']', tag, re.I)
        if cm:
            metas.append(("og:image", html.unescape(cm.group(1))))
    for m in re.finditer(r'<meta[^>]+name=["\']twitter:image["\'][^>]*>', body, re.I):
        tag=m.group(0)
        cm=re.search(r'content=["\']([^"\']+)["\']', tag, re.I)
        if cm:
            metas.append(("twitter:image", html.unescape(cm.group(1))))
    # json-ld image patterns simple
    for m in re.finditer(r'"image"\s*:\s*"([^"]+\.(?:jpg|jpeg|png|webp|gif)[^"]*)"', body, re.I):
        metas.append(("json-ld:image", m.group(1)))
    imgs=[]
    for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', body, re.I):
        src=html.unescape(m.group(1))
        src=urljoin(base_url, src)
        tag=m.group(0)
        altm=re.search(r'alt=["\']([^"\']*)["\']', tag, re.I)
        alt=altm.group(1) if altm else ""
        imgs.append((src, alt))
    return metas, imgs

results=[]
for idx, it in enumerate(items):
    key=it["key"]
    d=it["data"]
    srcUrl=d["sourceUrl"]
    srcName=d["sourceName"]
    sys.stdout.write(f"[{idx+1}/60] {key}\n")
    sys.stdout.flush()
    body, rc = curl_get_body(srcUrl)
    if body.startswith("ERROR"):
        title="FETCH ERROR"
        snippet=""
        metas=[]
        imgs=[]
    else:
        mt=re.search(r"<title[^>]*>(.*?)</title>", body, re.I|re.S)
        title=html.unescape(re.sub(r"<[^>]+>","", mt.group(1)).strip()) if mt else "NO TITLE"
        # avoid cp1252 print errors: encode safely
        safe_title=title.encode("ascii", errors="ignore").decode("ascii")
        sys.stdout.write(f"  title: {safe_title[:120]}\n")
        snippet=re.sub(r"<[^>]+>", " ", body)
        snippet=" ".join(snippet.split())[:1200]
        metas, imgs = extract_images(body, srcUrl)
        sys.stdout.write(f"  metas: {len(metas)} imgs: {len(imgs)}\n")
        for kind, url in metas[:2]:
            v=verify_url(url)
            sys.stdout.write(f"    VERIFY {url[:90]} => {v['code']} {v['ctype']} ok={v['ok']}\n")
        sys.stdout.flush()
    results.append({"key":key, "sourceUrl":srcUrl, "sourceName":srcName, "title":title if 'title' in locals() else "", "snippet": snippet if 'snippet' in locals() else "", "metas": metas, "imgs_sample": imgs[:5], "body_len": len(body)})
    time.sleep(0.6)

with open(out_path, "w", encoding="utf-8") as out:
    json.dump(results, out, ensure_ascii=False, indent=2)
print(f"Wrote {out_path}")
