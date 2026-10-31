"""Generate the made-up demo catalog: backend/data/catalog.json

All items, numbers and stock levels are invented for the hackathon demo.
Brand names appear only as nicknames, because that is what teams say out loud.

Run from the repo root:  python scripts/generate_catalog.py
"""

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.inventory.json_adapter import CatalogFile  # noqa: E402
from app.models import Item, Location, StockLevel  # noqa: E402

OUTPUT = ROOT / "backend" / "data" / "catalog.json"
rng = random.Random(42)  # fixed seed: same catalog every run

# ---------------------------------------------------------------- locations

LOCATIONS = [
    Location(id=f"OR-{n:02d}", name=f"Operating Room {n}", kind="or")
    for n in range(1, 13)
] + [
    Location(id="CORE-A", name="Core A (ORs 1-6)", kind="core"),
    Location(id="CORE-B", name="Core B (ORs 7-12)", kind="core"),
    Location(id="ORMC", name="OR Materials Core", kind="ormc"),
]
OR_IDS = [loc.id for loc in LOCATIONS if loc.kind == "or"]

# ---------------------------------------------------------------- items

items: list[dict] = []


def add(name, nicknames, category, unit="each", common=False):
    """Queue one item. common=True means ORs usually keep a few on hand."""
    items.append(
        {
            "name": name,
            "nicknames": [n.lower() for n in nicknames],
            "category": category,
            "unit": unit,
            "common": common,
        }
    )


# Sutures: material x size x needle
SUTURES = [
    ("Polyglactin Braided Absorbable Suture", ["vicryl", "vic"]),
    ("Polydioxanone Monofilament Absorbable Suture", ["pds"]),
    ("Poliglecaprone Monofilament Absorbable Suture", ["monocryl", "mono"]),
    ("Polypropylene Monofilament Suture", ["prolene", "pro"]),
    ("Silk Braided Suture", ["silk"]),
    ("Chromic Gut Suture", ["chromic", "gut"]),
    ("Nylon Monofilament Suture", ["nylon", "ethilon"]),
]
for material, nicks in SUTURES:
    for size in ["0", "2-0", "3-0", "4-0", "5-0"]:
        for needle in ["CT-1", "SH"]:
            add(
                f"{material} {size} {needle}",
                [f"{n} {size}" for n in nicks] + [f"{nicks[0]} {size} {needle}"],
                "Sutures",
                unit="box",
            )
for size in ["0", "2-0", "3-0"]:
    add(f"Silk Ties {size}, 18 in", [f"silk ties {size}", "free ties"], "Sutures", "pack")

# Gloves and gowns
GLOVES = [
    ("Sterile Surgical Gloves, Latex", ["gloves"]),
    ("Sterile Surgical Gloves, Latex-Free", ["latex free gloves", "non-latex gloves"]),
    ("Sterile Underglove, Latex-Free", ["underglove", "indicator gloves"]),
]
for name, nicks in GLOVES:
    for size in ["6", "6.5", "7", "7.5", "8", "8.5"]:
        add(f"{name}, Size {size}", [f"{n} {size}" for n in nicks], "Gloves", "box", common=True)
for name, nicks in [
    ("Surgical Gown, Standard", ["gown"]),
    ("Surgical Gown, Reinforced", ["reinforced gown", "impervious gown"]),
]:
    for size in ["L", "XL", "XXL"]:
        add(f"{name}, {size}", [f"{n} {size}" for n in nicks], "Gowns", common=True)

# Sponges
add("Laparotomy Sponge 18 x 18 in", ["laps", "lap pads", "lap sponges"], "Sponges", "pack", True)
add("Laparotomy Sponge 12 x 12 in", ["small laps"], "Sponges", "pack", True)
add("X-Ray Detectable Gauze Sponge 4 x 4 in", ["raytec", "4x4s", "ray tecs"], "Sponges", "pack", True)
add("Kittner Dissector Sponge", ["peanuts", "kittners", "peanut sponges"], "Sponges", "pack")
add("Tonsil Sponge", ["tonsil balls"], "Sponges", "pack")
for size in ["1/2 x 1/2 in", "1/2 x 3 in", "1 x 1 in", "1 x 3 in"]:
    add(f"Cottonoid Neuro Patty {size}", ["patties", "cottonoids", f"patties {size}"], "Sponges", "pack")

# Electrosurgery and energy
add("Electrosurgical Pencil, Rocker Switch", ["bovie", "cautery pencil", "bovie pencil"], "Electrosurgery", common=True)
add("Electrosurgical Pencil, Extended Blade", ["long bovie", "extended bovie"], "Electrosurgery")
add("Electrosurgical Pencil with Smoke Evacuation", ["smoke evac pencil", "smoke bovie"], "Electrosurgery")
add("Patient Return Electrode, Adult", ["grounding pad", "bovie pad", "return pad"], "Electrosurgery", common=True)
add("Patient Return Electrode, Pediatric", ["peds grounding pad"], "Electrosurgery")
add("Electrode Tip Cleaner", ["scratch pad", "tip cleaner"], "Electrosurgery", common=True)
add("Electrosurgical Needle Tip Electrode", ["needle tip bovie", "colorado tip"], "Electrosurgery")
add("Bipolar Forceps Cord", ["bipolar cord"], "Electrosurgery")
add("Bipolar Forceps, Disposable, Bayonet", ["bipolar", "bipolar forceps"], "Electrosurgery")
add("Ultrasonic Shears, 36 cm", ["harmonic", "harmonic scalpel"], "Energy Devices")
add("Ultrasonic Shears, 23 cm", ["short harmonic"], "Energy Devices")
add("Vessel Sealing Device, 37 cm", ["ligasure"], "Energy Devices")
add("Vessel Sealing Device, Open Jaw", ["ligasure impact", "open ligasure"], "Energy Devices")

# Instruments (sterile, single-use or loaner sets)
INSTRUMENTS = [
    ("Kocher Clamp, Straight", ["kocher", "kochers"]),
    ("Kelly Hemostat, Curved", ["kelly", "kellys"]),
    ("Crile Hemostat, Curved", ["crile"]),
    ("Mosquito Hemostat, Curved", ["mosquito", "snap"]),
    ("Allis Tissue Forceps", ["allis"]),
    ("Babcock Tissue Forceps", ["babcock"]),
    ("Right Angle Clamp", ["right angle", "mixter"]),
    ("Tonsil Clamp", ["tonsil", "schnidt"]),
    ("Mayo Scissors, Curved", ["mayos", "curved mayo"]),
    ("Metzenbaum Scissors", ["metz", "metzenbaums"]),
    ("Suture Scissors", ["suture scissors"]),
    ("DeBakey Tissue Forceps", ["debakey", "debakeys"]),
    ("Adson Tissue Forceps with Teeth", ["adson", "pickups", "adson with teeth"]),
    ("Russian Tissue Forceps", ["russians"]),
    ("Needle Holder, Mayo-Hegar", ["needle driver", "needle holder"]),
    ("Army-Navy Retractor", ["army navy", "army navys"]),
    ("Richardson Retractor", ["rich", "richardson"]),
    ("Deaver Retractor", ["deaver"]),
    ("Weitlaner Self-Retaining Retractor", ["weitlaner"]),
    ("Gelpi Self-Retaining Retractor", ["gelpi"]),
    ("Senn Retractor", ["senn", "cat paw"]),
    ("Malleable Retractor", ["malleable", "ribbon"]),
    ("Sponge Stick", ["sponge stick", "ring forceps"]),
    ("Towel Clip, Backhaus", ["towel clip"]),
]
for name, nicks in INSTRUMENTS:
    add(name, nicks, "Instruments")
for name, nicks in [
    ("Basic Laparotomy Instrument Set", ["lap set", "major set"]),
    ("Minor Instrument Set", ["minor set"]),
    ("Laparoscopic Instrument Set", ["lap chole set", "lappy set"]),
    ("Vascular Instrument Set", ["vascular set"]),
    ("Balfour Retractor Set", ["balfour"]),
    ("Bookwalter Retractor Set", ["bookwalter", "book"]),
]:
    add(name, nicks, "Instrument Sets", "set")

# Blades
for n in ["10", "11", "15", "20"]:
    add(f"Surgical Blade #{n}, Sterile", [f"{n} blade", f"#{n}"], "Blades", "box", common=True)
add("Scalpel Handle #3", ["knife handle", "3 handle"], "Blades")
add("Safety Scalpel #10, Disposable", ["disposable knife", "safety scalpel"], "Blades", "box")

# Staplers and clips
add("Skin Stapler, 35 Wide", ["skin stapler", "stapler"], "Staplers", common=True)
add("Skin Staple Remover", ["staple remover"], "Staplers")
for length in ["30", "45", "60"]:
    add(f"Endoscopic Linear Stapler {length} mm", [f"endo gia {length}", "endo stapler"], "Staplers")
    for color, tissue in [("Tan", "vascular"), ("Purple", "medium"), ("Black", "thick")]:
        add(
            f"Endoscopic Stapler Reload {length} mm, {color} ({tissue})",
            [f"{color.lower()} load {length}", f"{length} {color.lower()} reload", "reload"],
            "Staplers",
        )
for size in ["Small", "Medium", "Medium-Large", "Large"]:
    add(f"Ligating Clips, {size}", ["ligaclips", "clips", f"{size.lower()} clips"], "Clips", "box")
add("Clip Applier, Medium, Disposable", ["clip applier"], "Clips")
add("Endoscopic Clip Applier, 10 mm", ["endo clip", "lap clip applier"], "Clips")
add("Circular Stapler, 28 mm", ["eea 28", "circular stapler"], "Staplers")
add("Circular Stapler, 31 mm", ["eea 31"], "Staplers")

# Drains
for fr in ["7", "10", "15"]:
    add(f"Closed Wound Drain, Flat, {fr} Fr", ["jp", "jackson pratt", f"jp {fr}"], "Drains")
for fr in ["15", "19"]:
    add(f"Silicone Channel Drain {fr} Fr", ["blake", f"blake {fr}"], "Drains")
add("Bulb Reservoir, 100 mL", ["jp bulb", "grenade"], "Drains")
for size in ["1/4 in", "1/2 in", "1 in"]:
    add(f"Penrose Drain {size}", ["penrose", f"penrose {size}"], "Drains")
add("Closed Wound Suction Evacuator", ["hemovac"], "Drains")
add("Chest Tube 28 Fr", ["chest tube 28"], "Drains")
add("Chest Tube 32 Fr", ["chest tube 32"], "Drains")

# Catheters
for fr in ["14", "16", "18"]:
    add(f"Foley Catheter {fr} Fr, 5 mL Balloon", ["foley", f"foley {fr}"], "Catheters")
add("Foley Insertion Tray with Urine Meter", ["foley kit", "foley tray"], "Catheters", common=True)
add("Red Rubber Catheter 14 Fr", ["red rubber", "straight cath"], "Catheters")
add("Coude Catheter 16 Fr", ["coude"], "Catheters")

# Suction
add("Suction Connecting Tubing, 12 ft", ["suction tubing"], "Suction", common=True)
add("Yankauer Suction Tip", ["yankauer", "tonsil suction"], "Suction", common=True)
for fr in ["8", "10", "12"]:
    add(f"Frazier Suction Tip {fr} Fr", ["frazier", f"frazier {fr}"], "Suction")
add("Poole Abdominal Suction Tip", ["poole"], "Suction")
add("Suction Canister, 3000 mL", ["canister", "suction canister"], "Suction", common=True)
add("Suction Irrigator, Laparoscopic", ["suction irrigator", "lap suction"], "Suction")

# Dressings and skin closure
for size in ["2 3/8 x 2 3/4 in", "4 x 4 3/4 in", "6 x 8 in"]:
    add(f"Transparent Film Dressing {size}", ["tegaderm", f"tegaderm {size}"], "Dressings", "box")
for size in ["3 x 4 in", "3 x 8 in"]:
    add(f"Non-Adherent Pad {size}", ["telfa", f"telfa {size}"], "Dressings", "box")
add("Petrolatum Gauze 1 x 8 in", ["xeroform"], "Dressings", "box")
add("Petrolatum Gauze 5 x 9 in", ["big xeroform"], "Dressings", "box")
for size in ["1/4 x 4 in", "1/2 x 4 in"]:
    add(f"Adhesive Skin Closure Strips {size}", ["steri strips", "steris"], "Skin Closure", "box")
add("Topical Skin Adhesive, 0.7 mL", ["dermabond", "skin glue", "glue"], "Skin Closure", "box", True)
add("Liquid Adhesive Benzoin Swab", ["benzoin", "mastisol"], "Skin Closure", "box")
add("Abdominal Pad 8 x 10 in", ["abd", "abd pad"], "Dressings", "pack", True)
add("Gauze Roll 4.5 in", ["kerlix", "fluffs"], "Dressings", "pack")
add("Self-Adherent Wrap 4 in", ["coban"], "Dressings")
add("Antimicrobial Incise Drape 23 x 17 in", ["ioban"], "Drapes")
add("Island Dressing 4 x 8 in", ["island dressing", "primapore"], "Dressings", "box")
add("Foam Silicone Border Dressing 6 x 6 in", ["mepilex", "foam dressing"], "Dressings", "box")

# Drapes and covers
for name, nicks in [
    ("Laparotomy Drape, Transverse", ["lap drape"]),
    ("Universal Drape Pack", ["universal pack", "u drape"]),
    ("Split Sheet Drape", ["split sheet", "u drape"]),
    ("Extremity Drape", ["extremity drape"]),
    ("Three-Quarter Sheet", ["3/4 sheet", "three quarter sheet"]),
    ("Half Sheet", ["half sheet"]),
    ("Mayo Stand Cover", ["mayo cover", "mayo stand cover"]),
    ("Back Table Cover, 60 x 90 in", ["back table cover"]),
    ("C-Arm Drape", ["c arm drape", "c-arm cover"]),
    ("Camera Drape", ["camera bag", "camera cover"]),
    ("Light Handle Cover", ["light handles"]),
    ("Sterile Towels, Blue, 4 Pack", ["blue towels", "towels"]),
]:
    add(name, nicks, "Drapes", common=name.startswith(("Mayo", "Sterile Towels", "Light")))

# Hemostatics
add("Oxidized Regenerated Cellulose 2 x 3 in", ["surgicel", "surgicel small"], "Hemostatics", "box")
add("Oxidized Regenerated Cellulose 4 x 8 in", ["surgicel", "big surgicel"], "Hemostatics", "box")
add("Absorbable Gelatin Sponge, Size 100", ["gelfoam"], "Hemostatics", "box")
add("Hemostatic Matrix, 5 mL", ["floseal"], "Hemostatics", "box")
add("Bone Wax, 2.5 g", ["bone wax"], "Hemostatics", "box")
add("Topical Thrombin, 5000 units", ["thrombin"], "Hemostatics", "box")
add("Fibrin Sealant, 4 mL", ["tisseel", "fibrin glue"], "Hemostatics", "box")

# Laparoscopy
for mm in ["5", "11", "12"]:
    add(f"Bladeless Trocar {mm} mm, 100 mm", ["trocar", "port", f"{mm} port", f"{mm} trocar"], "Laparoscopy")
add("Hasson Trocar 12 mm", ["hasson"], "Laparoscopy")
add("Insufflation Needle 120 mm", ["veress", "veress needle"], "Laparoscopy")
add("Insufflation Tubing with Filter", ["insufflation tubing", "co2 tubing"], "Laparoscopy")
add("Specimen Retrieval Bag, 10 mm", ["endo catch", "bag", "specimen bag"], "Laparoscopy")
add("Specimen Retrieval Bag, 15 mm", ["big endo catch", "large bag"], "Laparoscopy")
add("Scope Anti-Fog Solution", ["fred", "defogger", "anti fog"], "Laparoscopy", common=True)
add("Scope Warmer", ["scope warmer"], "Laparoscopy")
add("Fascial Closure Device", ["carter thomason", "port closure"], "Laparoscopy")
add("Laparoscopic Maryland Dissector, 5 mm", ["maryland"], "Laparoscopy")
add("Laparoscopic Grasper, Atraumatic, 5 mm", ["grasper", "lap grasper"], "Laparoscopy")
add("Laparoscopic Scissors, Curved, 5 mm", ["lap scissors", "endo shears"], "Laparoscopy")
add("Laparoscopic L-Hook Electrode", ["hook", "l hook"], "Laparoscopy")

# Syringes, needles, irrigation
for ml in ["3", "5", "10", "20", "30"]:
    add(f"Luer-Lock Syringe {ml} mL", [f"{ml} cc syringe", f"{ml} ml syringe"], "Syringes", "box", True)
add("Catheter-Tip Syringe 60 mL", ["toomey", "60 cc catheter tip"], "Syringes", "box")
add("Bulb Irrigation Syringe 60 mL", ["asepto", "bulb syringe"], "Syringes", common=True)
for gauge in ["18", "22", "25", "27"]:
    add(f"Hypodermic Needle {gauge} G x 1.5 in", [f"{gauge} gauge", f"{gauge}g needle"], "Needles", "box")
add("Spinal Needle 22 G x 3.5 in", ["spinal needle"], "Needles", "box")
add("Sterile Saline for Irrigation 1000 mL", ["saline", "irrigation", "warm saline"], "Irrigation", common=True)
add("Sterile Saline for Irrigation 3000 mL", ["saline bag", "3 liter saline"], "Irrigation")
add("Sterile Water for Irrigation 1000 mL", ["sterile water", "water"], "Irrigation", common=True)
add("Pulse Lavage System", ["pulse lavage", "pulsavac"], "Irrigation")

# Prep, positioning, warming
add("Chlorhexidine Skin Prep Applicator 26 mL", ["chloraprep", "prep", "chg prep"], "Skin Prep", common=True)
add("Povidone-Iodine Prep Kit", ["betadine", "betadine prep"], "Skin Prep")
add("Surgical Skin Marker with Ruler", ["marker", "skin marker", "marking pen"], "Supplies", common=True)
add("Vessel Loops, Mini, Red", ["vessel loops", "loops", "red loops"], "Supplies", "pack")
add("Vessel Loops, Maxi, Blue", ["blue loops"], "Supplies", "pack")
add("Umbilical Tape, 1/8 in", ["umbilical tape", "umbi tape"], "Supplies", "pack")
add("Needle Counter Box, 40 Count", ["needle counter", "needle box"], "Supplies", common=True)
add("Forced-Air Warming Blanket, Upper Body", ["bair hugger", "upper bair"], "Warming")
add("Forced-Air Warming Blanket, Lower Body", ["lower bair", "bair hugger lower"], "Warming")
for size in ["Medium", "Large"]:
    add(f"Sequential Compression Sleeves, Knee, {size}", ["scds", f"scds {size.lower()}"], "Positioning")
add("Gel Head Ring, Adult", ["donut", "head donut"], "Positioning")
add("Foam Arm Board Pad", ["arm board pad", "egg crate"], "Positioning")
add("Safety Strap, Patient", ["safety strap", "belt"], "Positioning")
add("Specimen Container 120 mL", ["specimen cup"], "Supplies", common=True)
add("Biohazard Specimen Bag", ["specimen bag", "biohazard bag"], "Supplies", common=True)

# ---------------------------------------------------------------- stock


def make_stock(common: bool) -> list[StockLevel]:
    stock = []
    # ORMC holds most things; about 5% are out of stock there
    if rng.random() > 0.05:
        stock.append(StockLevel(location_id="ORMC", quantity=rng.randint(5, 200)))
    # Each core carries about 70% of items
    for core in ["CORE-A", "CORE-B"]:
        if rng.random() < 0.7:
            stock.append(StockLevel(location_id=core, quantity=rng.randint(1, 40)))
    # Common items also sit in a few ORs
    if common:
        for or_id in rng.sample(OR_IDS, rng.randint(2, 6)):
            stock.append(StockLevel(location_id=or_id, quantity=rng.randint(1, 10)))
    return stock


def main():
    catalog = CatalogFile(
        locations=LOCATIONS,
        items=[
            Item(
                item_number=f"SIF-{10001 + i}",
                mpn=f"MP-{rng.randint(100000, 999999)}",
                name=spec["name"],
                nicknames=spec["nicknames"],
                category=spec["category"],
                unit=spec["unit"],
                stock=make_stock(spec["common"]),
            )
            for i, spec in enumerate(items)
        ],
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(catalog.model_dump_json(indent=2), encoding="utf-8")
    print(f"Wrote {len(catalog.items)} items and {len(catalog.locations)} locations to {OUTPUT}")


if __name__ == "__main__":
    main()
