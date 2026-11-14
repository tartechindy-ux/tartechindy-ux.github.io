#!/usr/bin/env python3
"""Generate card art for Malfoid's Vault with Gemini "Nano Banana".

For every product in products.js that has no image yet:
  1. build a prompt from the product's description
     (kind "3d" = 3D render on a pedestal, kind "setting" = styled scene)
  2. generate 3 candidate images
  3. ask a Gemini vision model to pick the best one
  4. save the winner to art/<id>.jpg and record it in art/manifest.js

Needs:  GEMINI_API_KEY  (environment variable)   and   pip install pillow
Usage:  python scripts/generate_art.py              # only products missing art
        python scripts/generate_art.py --only slytherin-scarf --force
        python scripts/generate_art.py --dry-run    # print prompts, call nothing
"""
import argparse, base64, io, json, os, sys, time, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS = ROOT / "products.js"
MANIFEST = ROOT / "art" / "manifest.js"
ART_DIR = ROOT / "art"
PHOTO_DIR = ROOT / "my-photos"

IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "gemini-nano-banana-2.1")
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "gemini-3.1-flash-lite")
CANDIDATES = int(os.environ.get("CANDIDATES", "3"))
MAX_PER_RUN = int(os.environ.get("MAX_PER_RUN", "40"))   # spending cap per run
SIZE = 800
API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

STYLE = ("Dark, moody fantasy aesthetic with emerald green and silver accent lighting. "
         "Square 1:1 composition, the item centered and fully visible. "
         "No text, no lettering, no logos, no brand marks, no watermarks, no people's faces.")
PROMPTS = {
    "3d": ("A polished, high-detail 3D render of {desc}. The item sits on a dark stone pedestal "
           "like a collector's display piece, with soft studio lighting and a subtle reflection. "),
    "setting": ("A styled lifestyle scene featuring {desc}. The item is the clear focus, arranged "
                "naturally in a cozy gothic castle common room with stone walls and candlelight. "),
}
FROM_PHOTO = ("Recreate the exact item shown in the attached photo, keeping its real shape, colors "
              "and details accurate, as: ")


def load_js_json(path, opener, closer):
    text = path.read_text(encoding="utf-8")
    start = text.index("=", text.index("window.")) + 1
    body = text[start:].strip().rstrip(";").strip()
    assert body.startswith(opener) and body.endswith(closer), f"{path.name} is not valid"
    return json.loads(body)


def save_manifest(manifest):
    MANIFEST.write_text(
        "/* Written by scripts/generate_art.py. Maps product id -> image path. */\n"
        "window.ART = " + json.dumps(manifest, indent=1, sort_keys=True) + ";\n", encoding="utf-8")


def call(model, parts, config, key, tries=4):
    body = json.dumps({"contents": [{"parts": parts}], "generationConfig": config}).encode()
    req = urllib.request.Request(API.format(model=model), data=body, method="POST",
                                 headers={"Content-Type": "application/json", "x-goog-api-key": key})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:500]
            if e.code in (429, 500, 502, 503) and attempt < tries - 1:
                time.sleep(10 * (attempt + 1))
                continue
            raise RuntimeError(f"{model} returned HTTP {e.code}: {detail}") from None
        except urllib.error.URLError as e:
            if attempt < tries - 1:
                time.sleep(10 * (attempt + 1))
                continue
            raise RuntimeError(f"could not reach Gemini: {e.reason}") from None


def parts_of(resp):
    cands = resp.get("candidates") or []
    return (cands[0].get("content") or {}).get("parts") or [] if cands else []


def image_part(data, mime):
    return {"inlineData": {"mimeType": mime, "data": base64.b64encode(data).decode()}}


def build_prompt(p, has_photo):
    scene = PROMPTS.get(p.get("kind"), PROMPTS["3d"]).format(desc=p["desc"])
    return (FROM_PHOTO if has_photo else "") + scene + STYLE


def find_photo(pid):
    for ext, mime in ((".jpg", "image/jpeg"), (".jpeg", "image/jpeg"), (".png", "image/png")):
        f = PHOTO_DIR / (pid + ext)
        if f.exists():
            return f.read_bytes(), mime
    return None


def generate(p, key):
    photo = find_photo(p["id"])
    parts = [{"text": build_prompt(p, bool(photo))}]
    if photo:
        parts.append(image_part(*photo))
    images = []
    for n in range(CANDIDATES):
        resp = call(IMAGE_MODEL, parts, {"responseModalities": ["TEXT", "IMAGE"]}, key)
        for part in parts_of(resp):
            blob = part.get("inlineData") or part.get("inline_data")
            if blob and blob.get("data"):
                images.append(base64.b64decode(blob["data"]))
                break
        else:
            print(f"    candidate {n + 1}: no image returned", file=sys.stderr)
    return images


def pick_best(p, images, key):
    if len(images) == 1:
        return 0, "only one candidate"
    ask = (f"These are {len(images)} candidate images, in order, for a shop card showing: {p['desc']}. "
           "Pick the single best one. Prefer: the item is accurate to the description, clearly visible "
           "and well composed; no distorted shapes; and NO text, logos or watermarks anywhere. "
           'Reply as JSON: {"best": <number starting at 1>, "reason": "<short reason>"}')
    parts = [{"text": ask}] + [image_part(to_jpeg(img, 512), "image/jpeg") for img in images]
    try:
        resp = call(JUDGE_MODEL, parts, {"responseMimeType": "application/json"}, key)
        text = "".join(part.get("text", "") for part in parts_of(resp))
        verdict = json.loads(text)
        best = int(verdict["best"]) - 1
        if 0 <= best < len(images):
            return best, str(verdict.get("reason", ""))
    except Exception as e:  # judging is best-effort; never lose the images over it
        print(f"    judge failed ({e}); using candidate 1", file=sys.stderr)
    return 0, "judge unavailable, used first candidate"


def to_jpeg(data, size):
    from PIL import Image
    im = Image.open(io.BytesIO(data)).convert("RGB")
    w, h = im.size
    side = min(w, h)
    im = im.crop(((w - side) // 2, (h - side) // 2, (w + side) // 2, (h + side) // 2))
    im = im.resize((size, size), Image.LANCZOS)
    out = io.BytesIO()
    im.save(out, "JPEG", quality=85, optimize=True)
    return out.getvalue()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="generate just this product id")
    ap.add_argument("--force", action="store_true", help="regenerate even if art exists")
    ap.add_argument("--dry-run", action="store_true", help="print prompts without calling Gemini")
    args = ap.parse_args()

    products = load_js_json(PRODUCTS, "[", "]")
    manifest = load_js_json(MANIFEST, "{", "}") if MANIFEST.exists() else {}
    todo = [p for p in products
            if (not args.only or p["id"] == args.only)
            and (args.force or p["id"] not in manifest or not (ROOT / manifest[p["id"]]).exists())]
    if args.only and not todo and not any(p["id"] == args.only for p in products):
        sys.exit(f"No product with id {args.only!r} in products.js")
    if len(todo) > MAX_PER_RUN:
        print(f"{len(todo)} products need art; doing {MAX_PER_RUN} this run (MAX_PER_RUN).")
        todo = todo[:MAX_PER_RUN]
    if not todo:
        print("Every product already has art. Nothing to do.")
        return

    if args.dry_run:
        for p in todo:
            print(f"[{p['id']}] {build_prompt(p, bool(find_photo(p['id'])))}\n")
        print(f"{len(todo)} products x {CANDIDATES} candidates = {len(todo) * CANDIDATES} images.")
        return

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        sys.exit("Set the GEMINI_API_KEY environment variable first.")
    ART_DIR.mkdir(exist_ok=True)
    done = failed = 0
    for p in todo:
        print(f"[{p['id']}] generating {CANDIDATES} candidates...")
        try:
            images = generate(p, key)
            if not images:
                raise RuntimeError("no images came back")
            best, reason = pick_best(p, images, key)
            (ART_DIR / f"{p['id']}.jpg").write_bytes(to_jpeg(images[best], SIZE))
            manifest[p["id"]] = f"art/{p['id']}.jpg"
            save_manifest(manifest)          # save after each one so progress is never lost
            done += 1
            print(f"    picked candidate {best + 1} of {len(images)}: {reason}")
        except Exception as e:
            failed += 1
            print(f"    FAILED: {e}", file=sys.stderr)
    print(f"Done: {done} placed, {failed} failed.")
    if done == 0 and failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
