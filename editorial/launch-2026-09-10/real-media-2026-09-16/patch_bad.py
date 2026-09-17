#!/usr/bin/env python3
import json, re, subprocess, html, os, pathlib
from urllib.parse import urljoin

research_path="Z:/AnderZilla-docs/editorial/launch-2026-09-10/real-media-2026-09-16/research.json"
html_dir="Z:/AnderZilla-docs/editorial/launch-2026-09-10/real-media-2026-09-16/source-html"

with open(research_path, encoding="utf-8") as f:
    research=json.load(f)

# problematic keys to patch
targets=["logitech-mx-keypad","logitech-superstrike-clique","oppo-findx9ultra","oneplus15-165hz","typescript7-go","npm-trusted-publishing","github-secrets-merge","codeql-go127","claude-marca-texto","claude-cientistas"]

def verify(url):
    try:
        r=subprocess.run(["curl","-sL","-o","NUL","-w","%{http_code}:%{content_type}","-A","Mozilla/5.0 AnderZillaResearch/1.0","--max-time","15",url], capture_output=True, text=True, timeout=15)
        out=r.stdout.strip()
        code,ctype=out.split(":",1) if ":" in out else (out,"")
        return code=="200",code,ctype
    except:
        return False,"ERR",""

def extract_imgs(html_text, base):
    imgs=[]
    for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', html_text, re.I):
        src=html.unescape(m.group(1))
        src=urljoin(base, src)
        tag=m.group(0)
        altm=re.search(r'alt=["\']([^"\']*)["\']', tag, re.I)
        alt=altm.group(1) if altm else ""
        # also srcset
        srcsetm=re.search(r'srcset=["\']([^"\']+)["\']', tag, re.I)
        srcset=srcsetm.group(1) if srcsetm else ""
        imgs.append((src,alt,srcset))
    return imgs

for rec in research:
    key=rec["key"]
    if key not in targets:
        continue
    print(f"\nPatching {key}")
    html_path=os.path.join(html_dir, f"{key}.html")
    if not os.path.exists(html_path):
        print(f" no html {html_path}")
        continue
    with open(html_path, encoding="utf-8", errors="ignore") as f:
        body=f.read()
    sourcePage=rec["images"][0]["sourcePage"] if rec["images"] else rec.get("sourcePage","")
    # get base from sourcePage
    base=sourcePage
    imgs=extract_imgs(body, base)
    print(f"  raw imgs {len(imgs)}")
    # filter
    candidates=[]
    for src,alt,srcset in imgs:
        low=src.lower()
        # exclude obvious junk
        if low.endswith(".svg") or ".svg" in low:
            continue
        if "transparent.gif" in low:
            continue
        if "navigation" in low and "findx9ultra" not in low and "x9-ultra" not in low:
            # keep only if it's the hero? For oppo, navigation is junk
            continue
        if "featured-v3" in low: # github svgs
            continue
        if "emojis/heart.svg" in low:
            continue
        if "logitechg-bottom.svg" in low or "astro-bottom.svg" in low:
            continue
        if "oneplus15" in key and "arrow-r-red" in low:
            continue
        # must be image extension
        if not re.search(r'\.(jpg|jpeg|png|webp)(\?|&|$|")', low):
            # allow cdn urls with parameters like resource.logitechg.com without extension but with .../product/...png via path?
            # Check if contains /content/dam/ and includes image keyword
            if not ("/content/dam/" in low and any(x in low for x in ["superstrike","mx","product","gallery"])):
                continue
        # for logitech-superstrike, prioritize urls containing superstrike
        if key=="logitech-superstrike-clique" and "superstrike" not in low:
            # still allow but lower priority later; skip navigation
            if "gaming" in low and "navigation" in low:
                continue
        if key=="logitech-mx-keypad" and "mx" not in low and "keypad" not in low and "lexend" not in low and "businesswire" not in low:
            # keep if businesswire? but that was blocked; still consider but verify will fail
            # skip unless contains mx or keypad
            if not any(x in low for x in ["mx-","keypad","logitech"]):
                continue
        candidates.append((src,alt))
    print(f"  filtered {len(candidates)} candidates")
    for src,alt in candidates[:8]:
        print(f"    {src[:120]} alt:{alt[:60]}")
    # verify top candidates up to 3
    verified=[]
    for src,alt in candidates:
        if len(verified)>=3:
            break
        ok,code,ctype=verify(src)
        if ok:
            # avoid duplicates
            if src in [v[0] for v in verified]:
                continue
            verified.append((src,alt,code))
            print(f"    VERIFIED {code} {src[:80]}")
        else:
            # print fail
            pass
    # if we have verified, replace images
    if verified:
        # build new images list preserving first valid og if still valid?
        # For those with existing valid og, keep it as first, then add verified distinct
        # But our candidates include og? For typescript, og is https://devblogs.microsoft.com/typescript/wp-content/uploads/sites/11/2026/07/ts7-0-stable.png which should be in candidates and verified
        # So just rebuild
        old=rec["images"]
        # keep credit/rights from old if exists else default
        if old:
            credit=old[0]["credit"]
            rightsUrl=old[0]["rightsUrl"]
            rightsBasis=old[0]["rightsBasis"]
        else:
            credit=key
            rightsUrl=sourcePage
            rightsBasis="Official page"
        new_images=[]
        for idx,(src,alt,code) in enumerate(verified[:3]):
            kind=old[0]["kind"] if old else "photo"
            # infer kind again
            if key in ["typescript7-go","npm-trusted-publishing","github-secrets-merge","codeql-go127"]:
                kind="screenshot"
            elif key in ["logitech-mx-keypad","logitech-superstrike-clique","oppo-findx9ultra","oneplus15-165hz"]:
                kind="photo"
            elif key in ["claude-marca-texto","claude-cientistas"]:
                kind="diagram"
            new_images.append({
                "url": src,
                "sourcePage": sourcePage,
                "credit": credit,
                "rightsUrl": rightsUrl,
                "rightsBasis": rightsBasis,
                "altPT": rec["images"][0]["altPT"] if idx==0 and old else alt or f"Imagem de {key} {idx+1}",
                "altEN": rec["images"][0]["altEN"] if idx==0 and old else alt or f"Image of {key} {idx+1}",
                "kind": kind
            })
            # adjust alt suffix
            if idx>0:
                new_images[-1]["altPT"]=f"{new_images[0]['altPT']} – imagem {idx+1}"
                new_images[-1]["altEN"]=f"{new_images[0]['altEN']} – image {idx+1}"
        rec["images"]=new_images
        print(f"  => replaced with {len(new_images)} verified images")
    else:
        print(f"  No verified candidates, keeping original but will flag")
        # if all candidates failed, we should mark as fallback and clear images if original were bad
        # For logitech-mx-keypad, verified empty means no product photo found via filtered candidates, so status should be fallback?
        # Check if original images were bad svgs – they are svg but we didn't verify them as valid product; we should downgrade to fallback
        has_bad_svg = any(url.lower().endswith(".svg") for url in [i["url"].lower() for i in rec["images"]])
        if has_bad_svg:
            # check if we truly have no product photo, fallback
            if key=="logitech-mx-keypad":
                # attempt to keep as ready with note that Businesswire blocked but product photo exists elsewhere via manual check?
                # For now, mark fallback with reason
                rec["status"]="fallback"
                rec["reason"]="Varredura estática não encontrou foto de produto verificável para MX Keypad além de assets Businesswire bloqueados (000) e SVGs decorativos; og:image bloqueado. Nenhuma imagem JPG/PNG de produto verificada via GET 200 na varredura HTML. Requer press kit Logitech ou verificação manual."
                rec["images"]=[]
            if key=="logitech-superstrike-clique":
                # This one has alternatives but our filtered gave none? Let's check verified empty means no candidate passed
                # Keep fallback?
                rec["status"]="fallback"
                rec["reason"]="Produto Logitech PRO X2 SUPERSTRIKE: og:image é fallback transparente (transparent.gif) e varredura não isolou foto de produto verificável com filtro atual. Requer extração manual da galeria Logitech G."
                rec["images"]=[]

# Save patched
with open(research_path,"w",encoding="utf-8") as out:
    json.dump(research,out,ensure_ascii=False, indent=2)
print("\nPatched written")
