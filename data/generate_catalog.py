"""Generates the made-up demo catalog in data/catalog.json.

Everything here is invented for the hackathon demo: item numbers, stock levels
and floor plan. Run:  python data/generate_catalog.py
"""
from __future__ import annotations

import json
import random
from pathlib import Path

SEED = 20261030
OUT = Path(__file__).with_name("catalog.json")

# (name, category, nicknames, unit, variants)
# A variant list expands one base item into sizes, e.g. "Sterile Glove, Size {v}".
BASE_ITEMS = [
    # Sponges and dressings
    ("Laparotomy Sponge 18x18 in", "Sponges", ["lap sponge", "laps", "lap pad"], "pack of 5", None),
    ("Raytec Gauze Sponge 4x4 in", "Sponges", ["raytec", "4x4", "x-ray gauze"], "pack of 10", None),
    ("Kittner Dissector Sponge", "Sponges", ["kittner", "peanut", "peanut sponge"], "pack of 5", None),
    ("Cottonoid Patty {v}", "Sponges", ["cottonoid", "patty", "neuro patty"], "pack of 10", ["1/2 x 1/2 in", "1/2 x 3 in", "1 x 3 in"]),
    ("Transparent Film Dressing {v}", "Dressings", ["tegaderm", "clear dressing", "film dressing"], "each", ["2x3 in", "4x4 in", "4x10 in"]),
    ("Abdominal Pad 8x10 in", "Dressings", ["abd pad", "ABD", "combine"], "each", None),
    ("Island Dressing {v}", "Dressings", ["island dressing", "telfa island"], "each", ["4x4 in", "4x8 in", "4x14 in"]),
    ("Petrolatum Gauze 3x9 in", "Dressings", ["xeroform", "vaseline gauze"], "each", None),
    ("Skin Adhesive Topical 0.5 ml", "Dressings", ["dermabond", "skin glue", "glue"], "each", None),
    ("Skin Closure Strips {v}", "Dressings", ["steri-strips", "steris", "butterfly strips"], "pack", ["1/4 x 4 in", "1/2 x 4 in"]),
    # Sutures
    ("Absorbable Braided Suture {v}", "Sutures", ["vicryl", "polyglactin"], "box of 12",
     ["0 CT-1", "2-0 CT-1", "3-0 SH", "4-0 PS-2", "0 UR-6", "2-0 SH"]),
    ("Monofilament Absorbable Suture {v}", "Sutures", ["monocryl", "poliglecaprone"], "box of 12",
     ["3-0 PS-2", "4-0 PS-2", "4-0 P-3", "5-0 P-3"]),
    ("Polypropylene Suture {v}", "Sutures", ["prolene", "proline", "blue suture"], "box of 12",
     ["0 CT-1", "2-0 SH", "4-0 RB-1", "5-0 C-1", "6-0 C-1"]),
    ("Silk Suture {v}", "Sutures", ["silk", "black silk"], "box of 12", ["2-0 SH", "3-0 SH", "2-0 ties", "3-0 ties"]),
    ("Long-Term Absorbable Suture {v}", "Sutures", ["PDS", "pds plus", "polydioxanone"], "box of 12", ["0 CT-1", "1 CTX loop", "2-0 SH"]),
    ("Barbed Suture {v}", "Sutures", ["v-loc", "stratafix", "barbed"], "box of 12", ["3-0 15 cm", "2-0 30 cm"]),
    ("Chromic Gut Suture {v}", "Sutures", ["chromic", "gut"], "box of 12", ["3-0 SH", "4-0 RB-1"]),
    # Staplers and clips
    ("Skin Stapler 35W", "Staplers", ["skin stapler", "staple gun", "proximate"], "each", None),
    ("Linear Cutting Stapler {v}", "Staplers", ["GIA", "linear cutter"], "each", ["60 mm", "80 mm", "100 mm"]),
    ("Linear Stapler Reload {v}", "Staplers", ["GIA reload", "cartridge", "load"], "each", ["60 mm blue", "60 mm white", "80 mm blue", "80 mm green"]),
    ("Endoscopic Stapler Reload {v}", "Staplers", ["endo GIA reload", "tri-staple", "purple load", "tan load"], "each", ["45 mm tan", "45 mm purple", "60 mm purple", "60 mm black"]),
    ("Circular Stapler {v}", "Staplers", ["EEA", "circular", "anvil"], "each", ["25 mm", "28 mm", "31 mm"]),
    ("Ligating Clip Cartridge {v}", "Clips", ["hemoclip", "ligaclip", "clips"], "each", ["small", "medium", "medium-large", "large"]),
    ("Locking Polymer Clip Cartridge {v}", "Clips", ["hem-o-lok", "hemolock", "purple clips"], "each", ["ML", "L", "XL"]),
    ("Endoscopic Clip Applier 10 mm", "Clips", ["endo clip", "lap clip applier"], "each", None),
    # Electrosurgery and energy
    ("Electrosurgical Pencil with Holster", "Energy", ["bovie", "cautery", "bovie pencil", "pencil"], "each", None),
    ("Electrosurgical Grounding Pad", "Energy", ["grounding pad", "bovie pad", "return pad", "dispersive pad"], "each", None),
    ("Electrode Tip {v}", "Energy", ["bovie tip", "needle tip", "blade tip"], "each", ["blade 2.75 in", "blade 6 in", "needle", "ball 3 mm"]),
    ("Ultrasonic Shears {v}", "Energy", ["harmonic", "harmonic scalpel", "shears"], "each", ["23 cm", "36 cm"]),
    ("Vessel Sealing Device {v}", "Energy", ["ligasure", "sealer", "enseal"], "each", ["5 mm 37 cm", "Impact open"]),
    ("Bipolar Forceps Cord", "Energy", ["bipolar cord", "bipolar"], "each", None),
    ("Smoke Evacuation Pencil", "Energy", ["smoke evac", "smoke pencil"], "each", None),
    # Suction and irrigation
    ("Yankauer Suction Tip", "Suction", ["yankauer", "tonsil suction", "suction tip"], "each", None),
    ("Frazier Suction Tip {v}", "Suction", ["frazier", "frazier suction"], "each", ["8 Fr", "10 Fr", "12 Fr"]),
    ("Poole Abdominal Suction Tip", "Suction", ["poole", "poole suction"], "each", None),
    ("Suction Tubing 12 ft", "Suction", ["suction tubing", "suction line", "connecting tube"], "each", None),
    ("Suction Canister {v}", "Suction", ["canister", "liner"], "each", ["1500 ml", "3000 ml"]),
    ("Suction Irrigator Laparoscopic", "Suction", ["suction irrigator", "stryker flow", "lap suction"], "each", None),
    ("Bulb Irrigation Syringe 60 ml", "Irrigation", ["bulb syringe", "asepto", "turkey baster"], "each", None),
    ("Pulsed Lavage System", "Irrigation", ["pulsavac", "interpulse", "pulse lavage"], "each", None),
    ("Sterile Water for Irrigation {v}", "Irrigation", ["sterile water", "water"], "bottle", ["1000 ml", "3000 ml"]),
    ("Sodium Chloride for Irrigation {v}", "Irrigation", ["saline", "NS", "irrigation saline"], "bottle", ["500 ml", "1000 ml", "3000 ml"]),
    # Gloves and gowns
    ("Sterile Surgical Glove, Latex-Free, Size {v}", "Gloves", ["gloves", "biogel", "sterile gloves"], "pair", ["6", "6.5", "7", "7.5", "8", "8.5", "9"]),
    ("Sterile Underglove, Size {v}", "Gloves", ["indicator gloves", "underglove", "blue gloves"], "pair", ["6.5", "7", "7.5", "8"]),
    ("Surgical Gown, Reinforced, {v}", "Gowns", ["gown", "sterile gown"], "each", ["Large", "X-Large", "XX-Large"]),
    # Drapes and covers
    ("Incise Drape with Iodine {v}", "Drapes", ["ioban", "incise drape", "sticky drape"], "each", ["34x35 cm", "56x45 cm", "60x85 cm"]),
    ("Laparotomy Drape", "Drapes", ["lap drape"], "each", None),
    ("Extremity Drape", "Drapes", ["extremity drape", "arm drape", "leg drape"], "each", None),
    ("Split Sheet Drape", "Drapes", ["U drape", "split sheet"], "each", None),
    ("Mayo Stand Cover", "Drapes", ["mayo cover", "mayo bag"], "each", None),
    ("C-Arm Drape", "Drapes", ["c-arm cover", "fluoro drape"], "each", None),
    ("Camera Cover Sterile", "Drapes", ["camera bag", "camera sleeve", "scope cover"], "each", None),
    ("Back Table Cover 44x90 in", "Drapes", ["back table cover"], "each", None),
    ("Towel Drape Sterile 17x24 in", "Drapes", ["blue towels", "OR towels"], "pack of 4", None),
    # Blades and sharps
    ("Scalpel Blade #{v}", "Blades", ["blade", "knife blade"], "box of 10", ["10", "11", "15", "20"]),
    ("Disposable Scalpel #{v}", "Blades", ["scalpel", "knife"], "each", ["10", "11", "15"]),
    ("Needle Counter Box 20 count", "Blades", ["needle box", "sharps counter", "needle counter"], "each", None),
    ("Hypodermic Needle {v}", "Needles", ["needle"], "box of 100", ["18 G 1.5 in", "22 G 1.5 in", "25 G 1.5 in", "27 G 0.5 in"]),
    ("Syringe Luer-Lock {v}", "Syringes", ["syringe"], "each", ["3 ml", "5 ml", "10 ml", "20 ml", "60 ml"]),
    ("Spinal Needle {v}", "Needles", ["spinal needle", "quincke"], "each", ["22 G 3.5 in", "25 G 3.5 in"]),
    # Catheters, tubes, drains
    ("Foley Catheter {v}", "Catheters", ["foley", "urinary catheter", "cath"], "each", ["14 Fr", "16 Fr", "18 Fr", "20 Fr", "22 Fr"]),
    ("Foley Catheter Tray with Bag", "Catheters", ["foley kit", "cath kit", "foley tray"], "each", None),
    ("Endotracheal Tube Cuffed {v}", "Airway", ["ET tube", "ETT", "tube"], "each", ["6.0", "6.5", "7.0", "7.5", "8.0", "8.5"]),
    ("Laryngeal Mask Airway Size {v}", "Airway", ["LMA", "laryngeal mask"], "each", ["3", "4", "5"]),
    ("Oral Airway {v}", "Airway", ["oral airway", "OPA", "guedel"], "each", ["80 mm", "90 mm", "100 mm"]),
    ("Closed Wound Drain Round {v}", "Drains", ["blake drain", "blake", "round drain"], "each", ["15 Fr", "19 Fr", "24 Fr"]),
    ("Closed Suction Drain Reservoir 100 ml", "Drains", ["JP", "jackson-pratt", "JP bulb", "grenade"], "each", None),
    ("Wound Drain Flat {v}", "Drains", ["JP drain", "flat drain"], "each", ["7 mm", "10 mm"]),
    ("Chest Tube {v}", "Drains", ["chest tube", "thoracic catheter"], "each", ["24 Fr", "28 Fr", "32 Fr"]),
    ("Chest Drainage System", "Drains", ["pleur-evac", "atrium", "chest drain box"], "each", None),
    ("Penrose Drain {v}", "Drains", ["penrose"], "each", ["1/4 in", "1/2 in", "1 in"]),
    ("Nasogastric Tube {v}", "Catheters", ["NG tube", "salem sump", "NGT"], "each", ["14 Fr", "16 Fr", "18 Fr"]),
    ("Vessel Loops {v}", "Retraction", ["vessel loops", "vessel loop"], "pack of 2", ["red mini", "blue mini", "yellow maxi", "white maxi"]),
    ("Umbilical Tape 1/8 x 30 in", "Retraction", ["umbilical tape", "umbi tape"], "each", None),
    # Laparoscopy
    ("Trocar with Blunt Tip {v}", "Laparoscopy", ["trocar", "port", "hasson"], "each", ["5 mm", "11 mm", "12 mm"]),
    ("Optical Trocar {v}", "Laparoscopy", ["optiview", "optical port", "visiport"], "each", ["5 mm", "12 mm"]),
    ("Insufflation Tubing with Filter", "Laparoscopy", ["insufflation tubing", "CO2 tubing", "gas tubing"], "each", None),
    ("Veress Needle 120 mm", "Laparoscopy", ["veress", "insufflation needle"], "each", None),
    ("Specimen Retrieval Bag {v}", "Laparoscopy", ["endo catch", "specimen bag", "endo bag"], "each", ["10 mm", "15 mm"]),
    ("Anti-Fog Solution Kit", "Laparoscopy", ["fred", "defogger", "anti-fog"], "each", None),
    ("Fascial Closure Device", "Laparoscopy", ["carter-thomason", "port closure"], "each", None),
    # Hemostats and biologics
    ("Oxidized Cellulose Hemostat {v}", "Hemostats", ["surgicel", "surgicel fibrillar"], "each", ["2x3 in", "4x8 in", "fibrillar 2x4 in"]),
    ("Absorbable Gelatin Sponge {v}", "Hemostats", ["gelfoam", "gel foam"], "each", ["size 100", "size 12-7 mm"]),
    ("Thrombin Topical Kit 5000 units", "Hemostats", ["thrombin", "recothrom"], "each", None),
    ("Hemostatic Matrix 5 ml", "Hemostats", ["floseal", "surgiflo"], "each", None),
    ("Fibrin Sealant 4 ml", "Hemostats", ["tisseel", "evicel", "fibrin glue"], "each", None),
    ("Bone Wax 2.5 g", "Hemostats", ["bone wax", "horsley wax"], "each", None),
    # Orthopedics
    ("Kirschner Wire {v}", "Orthopedics", ["k-wire", "kwire", "pin"], "each", ["0.035 in", "0.045 in", "0.062 in"]),
    ("Steinmann Pin {v}", "Orthopedics", ["steinmann", "pin"], "each", ["3/32 in", "1/8 in"]),
    ("Saw Blade Sagittal {v}", "Orthopedics", ["saw blade", "sagittal blade"], "each", ["small", "large"]),
    ("Bone Cement 40 g", "Orthopedics", ["cement", "PMMA", "simplex"], "each", None),
    ("Cement Mixing System", "Orthopedics", ["cement mixer", "mix kit"], "each", None),
    ("Tourniquet Cuff {v}", "Orthopedics", ["tourniquet", "cuff"], "each", ["18 in", "24 in", "34 in"]),
    ("Cast Padding {v}", "Orthopedics", ["webril", "cast padding"], "roll", ["3 in", "4 in", "6 in"]),
    ("Elastic Bandage {v}", "Orthopedics", ["ace wrap", "ACE", "ace bandage"], "roll", ["4 in", "6 in"]),
    ("Splint Roll Fiberglass {v}", "Orthopedics", ["ortho-glass", "splint"], "roll", ["3 in", "4 in", "5 in"]),
    # Skin prep and misc
    ("Chlorhexidine Skin Prep 26 ml", "Skin Prep", ["chloraprep", "chg prep", "orange prep"], "each", None),
    ("Povidone-Iodine Prep Kit", "Skin Prep", ["betadine", "iodine prep", "betadine kit"], "each", None),
    ("Surgical Clipper Blade", "Skin Prep", ["clipper blade", "hair clipper"], "each", None),
    ("Surgical Skin Marker with Ruler", "Misc", ["marker", "skin marker", "sharpie"], "each", None),
    ("Light Handle Cover", "Misc", ["light handle", "light cover"], "each", None),
    ("Specimen Container {v}", "Misc", ["specimen cup", "path cup"], "each", ["120 ml", "1000 ml"]),
    ("Sequential Compression Sleeves {v}", "Misc", ["SCDs", "SCD sleeves", "compression sleeves"], "pair", ["knee medium", "thigh medium", "thigh large"]),
    ("Warming Blanket Upper Body", "Misc", ["bair hugger", "bear hugger", "warming blanket"], "each", None),
    ("Positioning Gel Pad Set", "Misc", ["gel pads", "positioners"], "set", None),
    ("Foam Head Positioner", "Misc", ["donut", "foam donut", "head ring"], "each", None),
    ("Wound Protector Retractor {v}", "Retraction", ["alexis", "wound protector", "ring retractor"], "each", ["small", "medium", "large"]),
    ("Lone Star Retractor Hooks", "Retraction", ["lone star hooks", "stays"], "pack of 8", None),
    # More common requests
    ("Sterile Orthopedic Glove, Size {v}", "Gloves", ["ortho gloves", "thick gloves"], "pair", ["7", "7.5", "8", "8.5"]),
    ("Nylon Monofilament Suture {v}", "Sutures", ["ethilon", "nylon", "black nylon"], "box of 12", ["3-0 FS-1", "4-0 PS-2", "5-0 P-3"]),
    ("Peripheral IV Catheter {v}", "Catheters", ["IV", "angiocath", "jelco"], "each", ["14 G", "16 G", "18 G", "20 G", "22 G"]),
    ("Arterial Line Kit 20 G", "Catheters", ["art line", "a-line kit"], "each", None),
    ("Central Line Kit Triple Lumen 7 Fr", "Catheters", ["central line", "CVC kit", "triple lumen"], "each", None),
    ("IV Administration Set with Pump Cassette", "IV", ["IV tubing", "pump tubing", "primary tubing"], "each", None),
    ("Blood Warmer Set", "IV", ["blood tubing", "level 1 set", "warmer tubing"], "each", None),
    ("Pressure Transducer Kit {v}", "IV", ["transducer", "art line transducer"], "each", ["single", "double"]),
    ("Laparoscopic Grasper {v}", "Laparoscopy", ["grasper", "maryland", "lap grasper"], "each", ["Maryland 5 mm", "atraumatic 5 mm", "claw 10 mm"]),
    ("Laparoscopic Scissors Curved 5 mm", "Laparoscopy", ["lap scissors", "endo shears"], "each", None),
    ("Hernia Mesh Polypropylene {v}", "Implants", ["mesh", "prolene mesh", "hernia mesh"], "each", ["3x6 in", "6x6 in", "12x12 in"]),
    ("Hernia Mesh Fixation Tacker 5 mm", "Implants", ["tacker", "protack", "absorbatack"], "each", None),
    ("Cortical Bone Screw 3.5 mm {v}", "Implants", ["cortex screw", "3.5 screw"], "each", ["14 mm", "18 mm", "22 mm", "26 mm"]),
    ("Drill Bit {v}", "Orthopedics", ["drill bit", "bit"], "each", ["2.5 mm", "3.2 mm"]),
    ("Electrosurgical Pencil Extension Cord", "Energy", ["bovie extension"], "each", None),
    ("Ultrasound Probe Cover Sterile", "Drapes", ["probe cover", "ultrasound sleeve"], "each", None),
    ("Microscope Drape", "Drapes", ["scope drape", "microscope cover"], "each", None),
    ("Telfa Non-Adherent Pad {v}", "Dressings", ["telfa", "non-stick pad"], "each", ["3x4 in", "3x8 in"]),
    ("Fluff Gauze Roll 4.5 in", "Dressings", ["kerlix", "fluff roll", "kling"], "roll", None),
    ("Silk Tape {v}", "Dressings", ["silk tape", "durapore", "tape"], "roll", ["1 in", "2 in"]),
    # Instruments (sterile peel packs)
    ("Kocher Clamp Straight 8 in", "Instruments", ["kocher", "kocker", "ochsner"], "each", None),
    ("Kelly Hemostat Curved 5.5 in", "Instruments", ["kelly", "kelly clamp", "hemostat"], "each", None),
    ("Mosquito Hemostat Curved 5 in", "Instruments", ["mosquito", "snap", "mosquito clamp"], "each", None),
    ("Right Angle Clamp 9 in", "Instruments", ["right angle", "mixter", "RA clamp"], "each", None),
    ("Allis Tissue Forceps 6 in", "Instruments", ["allis", "alice clamp"], "each", None),
    ("Babcock Forceps 8 in", "Instruments", ["babcock"], "each", None),
    ("Metzenbaum Scissors Curved 7 in", "Instruments", ["metz", "metzenbaum", "metz scissors"], "each", None),
    ("Mayo Scissors Straight 6.75 in", "Instruments", ["mayo scissors", "straight mayo", "suture scissors"], "each", None),
    ("Needle Holder Mayo-Hegar 7 in", "Instruments", ["needle driver", "needle holder", "hegar"], "each", None),
    ("DeBakey Forceps 8 in", "Instruments", ["debakey", "debakeys", "atraumatic forceps"], "each", None),
    ("Adson Forceps with Teeth", "Instruments", ["adson", "adsons", "pickups with teeth"], "each", None),
    ("Army-Navy Retractor Pair", "Instruments", ["army navy", "army-navys", "USA retractor"], "pair", None),
    ("Richardson Retractor Medium", "Instruments", ["rich", "richardson"], "each", None),
    ("Deaver Retractor 1.5 in", "Instruments", ["deaver"], "each", None),
    ("Weitlaner Retractor 6.5 in", "Instruments", ["weitlaner", "self-retainer", "weitty"], "each", None),
    ("Towel Clip Backhaus 5.25 in", "Instruments", ["towel clip", "backhaus", "penetrating towel clamp"], "each", None),
    ("Sponge Stick Forceps 9.5 in", "Instruments", ["sponge stick", "ring forceps", "foerster"], "each", None),
]

LOCATIONS = (
    [{"id": f"OR-{n:02d}", "name": f"OR {n} Supply Cart", "type": "or",
      "x": 10.0 + ((n - 1) % 6) * 12, "y": 0.0 if n <= 6 else 30.0, "serves": [f"OR-{n:02d}"]}
     for n in range(1, 13)]
    + [
        {"id": "CORE-A", "name": "Core A (serves OR 1-6)", "type": "core", "x": 40.0, "y": 10.0,
         "serves": [f"OR-{n:02d}" for n in range(1, 7)]},
        {"id": "CORE-B", "name": "Core B (serves OR 7-12)", "type": "core", "x": 40.0, "y": 20.0,
         "serves": [f"OR-{n:02d}" for n in range(7, 13)]},
        {"id": "ORMC", "name": "ORMC Main Supply Room", "type": "ormc", "x": 90.0, "y": 15.0, "serves": []},
    ]
)


def build() -> dict:
    rng = random.Random(SEED)
    items, stock = [], []
    used_numbers: set[str] = set()

    for name, category, nicknames, unit, variants in BASE_ITEMS:
        for variant in variants or [None]:
            item_id = f"ITM-{len(items) + 1:04d}"
            number = str(rng.randint(100000, 999999))
            while number in used_numbers:
                number = str(rng.randint(100000, 999999))
            used_numbers.add(number)
            items.append({
                "id": item_id,
                "item_number": number,
                "name": name.format(v=variant) if variant else name,
                "category": category,
                "nicknames": nicknames,
                "unit": unit,
                "image_url": None,
            })

            # ORMC stocks everything. Cores stock most items. OR carts stock a few.
            stock.append({"item_id": item_id, "location_id": "ORMC",
                          "quantity": rng.randint(20, 200), "bin": f"R{rng.randint(1, 30)}-S{rng.randint(1, 6)}"})
            for core in ("CORE-A", "CORE-B"):
                if rng.random() < 0.75:
                    stock.append({"item_id": item_id, "location_id": core,
                                  "quantity": rng.randint(0, 40), "bin": f"{core[-1]}{rng.randint(1, 12)}-{rng.randint(1, 5)}"})
            for n in range(1, 13):
                if rng.random() < 0.12:
                    stock.append({"item_id": item_id, "location_id": f"OR-{n:02d}",
                                  "quantity": rng.randint(0, 6), "bin": f"Drawer {rng.randint(1, 6)}"})

    return {
        "_note": "Made-up data for the Surgical Item Finder hackathon demo. Not real hospital data.",
        "items": items,
        "locations": LOCATIONS,
        "stock": stock,
    }


if __name__ == "__main__":
    catalog = build()
    OUT.write_text(json.dumps(catalog, indent=1) + "\n")
    print(f"Wrote {len(catalog['items'])} items, {len(catalog['locations'])} locations, "
          f"{len(catalog['stock'])} stock rows to {OUT}")
