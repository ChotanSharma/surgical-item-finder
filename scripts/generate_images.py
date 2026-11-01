"""Create a product photo for each catalog item with Meta's Muse Image model.

Uses API credit, so it starts small. Run from the repo root:
    python scripts/generate_images.py SIF-10107 SIF-10098   # just these items
    python scripts/generate_images.py              # the next 2 items without a photo
    python scripts/generate_images.py --limit 300  # the rest

Items that already have a photo are skipped, so it is safe to run again.
"""

import argparse
import base64
import io
import sys
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.inventory.json_adapter import JsonAdapter  # noqa: E402
from app.llm import get_client  # noqa: E402

CATALOG = ROOT / "backend" / "data" / "catalog.json"
IMAGES = ROOT / "backend" / "data" / "images"
IMAGE_MODEL = "muse-image-1.0"
SIZE = 320  # pixels; small WebP files keep the repo light (about 10 KB each)


def prompt_for(item) -> str:
    # The sealed package as it sits on a supply shelf, so ORMC staff can spot it.
    # Generic packaging only: no readable text, brands or logos.
    return (
        f"Product photo of the sealed sterile packaging for a {item.name} "
        f"({item.category.lower()}), exactly as it is stored on a hospital supply shelf: "
        "for example a peel pouch, blister pack, box or wrapped pack, whichever fits this item. "
        f"Sold per {item.unit}. Plain white background, soft studio lighting, realistic, centered. "
        "Blank labels with no readable text, no brand names, no logos, no people."
    )


def save_webp(raw: bytes, path: Path) -> None:
    image = Image.open(io.BytesIO(raw)).convert("RGB")
    image.thumbnail((SIZE, SIZE))
    image.save(path, "WEBP", quality=80)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("items", nargs="*", help="only these item numbers")
    parser.add_argument("--limit", type=int, default=2, help="max images to create this run")
    parser.add_argument("--dry-run", action="store_true", help="print prompts, call nothing")
    args = parser.parse_args()

    IMAGES.mkdir(parents=True, exist_ok=True)
    todo = [i for i in JsonAdapter(CATALOG).list_items() if not (IMAGES / f"{i.item_number}.webp").exists()]
    if args.items:
        todo = [i for i in todo if i.item_number in args.items]
    print(f"{len(todo)} items still need a photo; making up to {args.limit}.")

    client = None if args.dry_run else get_client()
    made = 0
    for item in todo[: args.limit]:
        prompt = prompt_for(item)
        if args.dry_run:
            print(f"{item.item_number}: {prompt}")
            continue
        try:
            result = client.images.generate(model=IMAGE_MODEL, prompt=prompt)
            picture = result.data[0]
            if picture.b64_json:
                raw = base64.b64decode(picture.b64_json)
            else:
                with urllib.request.urlopen(picture.url) as response:
                    raw = response.read()
            save_webp(raw, IMAGES / f"{item.item_number}.webp")
            made += 1
            print(f"  ok  {item.item_number}  {item.name}")
        except Exception as error:  # keep going; one bad image shouldn't stop the run
            print(f"  failed  {item.item_number}: {error}")
    print(f"Done: {made} new photos in {IMAGES}")


if __name__ == "__main__":
    main()
