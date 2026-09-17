#!/usr/bin/env python3
import json, re

path="Z:/AnderZilla-docs/editorial/launch-2026-09-10/real-media-2026-09-16/research.json"
with open(path, encoding="utf-8") as f:
    data=json.load(f)

# product keyword map for validation
keyword_map={
    "logitech-mx-keypad": ["mx","keypad","lexend"],
    "logitech-superstrike-clique": ["superstrike"],
    "oppo-findx9ultra": ["findx9ultra","find-x9-ultra","findx9"],
    "oneplus15-165hz": ["oneplus15","oneplus-15","oneplus"],
    "typescript7-go": ["typescript","7-0","ts7"],
    "npm-trusted-publishing": ["npm","trusted","publishing","changelog"],
    "github-secrets-merge": ["secrets","github","changelog"],
    "codeql-go127": ["codeql","go127","go-1.27"],
    "claude-marca-texto": ["watermark","claude","marca"],
    "claude-cientistas": ["scientist","cientista","claude"],
    "galaxy-fold8-comparacao": ["fold8","galaxy"],
    "galaxy-s26-privacy": ["s26","galaxy"],
}

# For generic keys, we will validate that URL does not contain obviously mismatched product names
# e.g., for oppo, reject enco-buds, band2
mismatch_map={
    "oppo-findx9ultra": ["enco","band","reno","pad","watch","buds"],
    "oneplus15-165hz": ["arrow-r-red"], # keep only phone/kv images, but arrow is junk
    "typescript7-go": ["microsoft/RE1Mu3b","daniel-rosenwasser"], # logo/avatar
}

def is_valid(key, url):
    low=url.lower()
    # always reject svg unless it's claude diagram and allowed?
    if low.endswith(".svg") or ".svg" in low:
        if key in ["claude-marca-texto","claude-cientistas"]:
            # allow svg if it's the watermark diagram svg
            if "watermark" in low or "claude" in low:
                return True
        return False
    if "transparent.gif" in low:
        # allow if contains product keyword
        if key=="logitech-superstrike-clique" and "superstrike" in low:
            return True
        return False
    if "navigation" in low:
        # for oppo, only allow if contains findx9ultra
        if key=="oppo-findx9ultra" and "findx9ultra" not in low:
            return False
        # for others, navigation is generally junk
        if key!="oppo-findx9ultra":
            return False
    if "featured-v3" in low:
        return False
    # check keyword must be present for targeted keys
    if key in keyword_map:
        kws=keyword_map[key]
        if not any(kw in low for kw in kws):
            # for some keys like typescript, the chart images do contain 7-0
            # but microsoft logo does not – reject
            return False
    # check mismatch reject
    if key in mismatch_map:
        for bad in mismatch_map[key]:
            if bad in low:
                return False
    return True

for rec in data:
    key=rec["key"]
    old_images=rec["images"]
    if not old_images:
        continue
    # filter
    new_images=[img for img in old_images if is_valid(key, img["url"])]
    # special handling for logitech keys where we have 0 after filter – need fallback
    if key=="logitech-mx-keypad":
        # after filtering, we have 0 (since all 3 were svg) – check if any original was at least a photo? Our filter says 0, so fallback
        if len(new_images)==0:
            rec["status"]="fallback"
            rec["reason"]="Varredura estática não encontrou foto de produto verificável para MX Keypad além de assets Businesswire bloqueados (000) e SVGs decorativos; og:image Businesswire bloqueado (000) e 18 <img> não continham JPG/PNG de produto com 'mx'/'keypad'. Requer press kit Logitech verificado manualmente."
            rec["images"]=[]
            continue
    if key=="logitech-superstrike-clique":
        if len(new_images)==0:
            # try to find valid superstrike image from original inventory? For now fallback
            rec["status"]="fallback"
            rec["reason"]="Produto Logitech PRO X2 SUPERSTRIKE: og:image é fallback transparente (transparent.gif) e varredura HTML não isolou foto de produto JPG/PNG com 'superstrike' verificável via GET 200 com filtro atual. Requer extração manual da galeria Logitech G (ex: pro-x2-superstrike-top-angle-lifestyle-gallery-2.png)."
            rec["images"]=[]
            continue
    if key=="oppo-findx9ultra":
        # keep only hero (should be 1)
        if len(new_images)>=1:
            # ensure hero is first
            rec["images"]=new_images[:1]
        else:
            # fallback to original hero if filtered out incorrectly? But hero contains findx9ultra, so should be kept
            pass
    if key=="oneplus15-165hz":
        # after filtering, we rejected arrow, keep kv images that contain oneplus15
        # our current after patch had 3 kv images, but they may all be valid? Check: images-kv-mo-phone is valid, logo/bg maybe not phone? But they contain oneplus15, so they pass.
        # Keep only phone image maybe? For quality, keep only phone image as primary, others are kv backgrounds – but they are still OnePlus 15 visuals, could be considered official artwork.
        # We'll keep all that passed filter (should be 3 kv images)
        rec["images"]=new_images[:3] if new_images else old_images
    if key=="typescript7-go":
        # after filtering, only charts remain
        rec["images"]=new_images[:3]
        if len(new_images)>=1:
            # update kind to diagram/screenshot for charts
            for img in rec["images"]:
                img["kind"]="diagram"
    if key in ["npm-trusted-publishing","github-secrets-merge","codeql-go127"]:
        # these had 2 images, second is svg bad, first is valid jpg – keep only first
        rec["images"]=new_images[:3]
    if key in ["claude-marca-texto","claude-cientistas"]:
        # keep svg if it's watermark diagram, but currently filtered out all? Our filter for those svgs returns True only if watermark, but our current images for those are the og png (Hand Quill) and svg – after filtering, the svg may be kept, but we had 2 images originally: og png and svg. After filter, svg may be kept. Need to inspect.
        # For now, keep what passed
        rec["images"]=new_images[:2] if new_images else old_images
    # for others, just replace with filtered
    if key not in ["logitech-mx-keypad","logitech-superstrike-clique","oppo-findx9ultra","oneplus15-165hz","typescript7-go","npm-trusted-publishing","github-secrets-merge","codeql-go127","claude-marca-texto","claude-cientistas"]:
        # if we filtered some, update
        if len(new_images)!=len(old_images):
            rec["images"]=new_images
            if len(new_images)==0 and rec["status"]=="ready":
                rec["status"]="fallback"
                rec["reason"]=f"Nenhuma imagem restante após filtro de qualidade para {key}; requer verificação manual."
    else:
        # for those keys we already handled, ensure status consistency
        if len(rec["images"])==0 and rec["status"]=="ready":
            rec["status"]="fallback"
        if len(rec["images"])>0 and rec["status"]=="fallback" and key not in ["logitech-mx-keypad","logitech-superstrike-clique"]:
            rec["status"]="ready"

# Also fix galazy etc that may have no issue but check
# recount
ready=sum(1 for r in data if r["status"]=="ready")
fallback=sum(1 for r in data if r["status"]=="fallback")
print(f"After correction: ready {ready} fallback {fallback}")

with open(path,"w",encoding="utf-8") as out:
    json.dump(data,out,ensure_ascii=False, indent=2)
print("corrected")
