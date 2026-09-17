#!/usr/bin/env python3
# Preliminary sweep: fetch each sourceUrl, extract og:image/twitter, verify HEAD
import json, re, subprocess, html, time, os, sys
from urllib.parse import urljoin, urlparse

manifest_path = "Z:/AnderZilla-docs/editorial/launch-2026-09-10/launch-manifest.json"
out_path = "Z:/AnderZilla-docs/editorial/launch-2026-09-10/real-media-2026-09-16/research_prelim.json"

with open(manifest_path, encoding="utf-8") as f:
    data=json.load(f)

items=data["items"]

def curl_get(url):
    try:
        r=subprocess.run(["curl","-sL","-A","Mozilla/5.0 (Windows NT 10.0; Win64; x64) AnderZillaResearch/1.0","--max-time","20","--compressed",url], capture_output=True, timeout=25)
        body=r.stdout.decode("utf-8", errors="ignore")
        return body, r.returncode
    except Exception as e:
        return f"ERROR: {e}", 1

def curl_head(url):
    try:
        r=subprocess.run(["curl","-sI","-L","-A","Mozilla/5.0 AnderZillaResearch/1.0","--max-time","15",url], capture_output=True, timeout=20)
        txt=r.stdout.decode("utf-8", errors="ignore")
        # find last status
        statuses=re.findall(r"HTTP/[^\r\n]+", txt)
        last=statuses[-1] if statuses else ""
        ok="200" in last
        ct=re.search(r"content-type:\s*([^\r\n]+)", txt, re.I)
        ct=ct.group(1).strip() if ct else ""
        cl=re.search(r"content-length:\s*([^\r\n]+)", txt, re.I)
        cl=cl.group(1).strip() if cl else ""
        return {"status":last, "ok": ok, "content_type": ct, "raw": txt[:2000]}
    except Exception as e:
        return {"status": f"ERROR {e}", "ok": False, "content_type": "", "raw": ""}

def extract_images(body, base_url):
    # find og:image
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
    # also json-ld image
    for m in re.finditer(r'"image"\s*:\s*"([^"]+)"', body):
        metas.append(("json-ld:image", m.group(1)))
    for m in re.finditer(r'"image"\s*:\s*\[\s*"([^"]+)"', body):
        metas.append(("json-ld:image-array", m.group(1)))
    # find all <img src>
    imgs=[]
    for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', body, re.I):
        src=html.unescape(m.group(1))
        # resolve relative
        src=urljoin(base_url, src)
        # collect alt if present
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
    print(f"[{idx+1}/60] {key} => {srcUrl}")
    body, rc = curl_get(srcUrl)
    if body.startswith("ERROR"):
        print("  fetch error")
        metas=[]
        imgs=[]
        title="FETCH ERROR"
    else:
        mt=re.search(r"<title[^>]*>(.*?)</title>", body, re.I|re.S)
        title=html.unescape(re.sub(r"<[^>]+>","", mt.group(1)).strip()) if mt else "NO TITLE"
        # shorten snippet for check factual correspondence
        snippet=re.sub(r"<[^>]+>", " ", body)
        snippet=" ".join(snippet.split())[:1200]
        # Detect if page is generic archive or 404-like
        # check if topic keywords present?
        metas, imgs = extract_images(body, srcUrl)
        print(f"  title: {title[:120]}")
        print(f"  metas: {metas[:3]} len imgs tags: {len(imgs)}")
        # try to verify first og image HEAD
        for kind, url in metas[:1]:
            h=curl_head(url)
            print(f"    HEAD {url[:100]} => {h['status']} ct:{h['content_type']}")
    # also record snippet start for later analysis
    results.append({"key":key, "sourceUrl":srcUrl, "sourceName":srcName, "title":title if 'title' in locals() else "", "snippet": snippet if 'snippet' in locals() else "", "metas": metas, "imgs_sample": imgs[:5], "body_len": len(body) if 'body' in locals() else 0})
    time.sleep(0.8)

with open(out_path, "w", encoding="utf-8") as out:
    json.dump(results, out, ensure_ascii=False, indent=2)
print(f"Wrote {out_path}")
