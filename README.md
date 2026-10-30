# Surgical Item Finder

**An AI agent that gets the right surgical supply to the operating room, without a phone call.**

Built solo for the **Meta Global AI Developer Hackathon** (Oct 26 to Nov 4, 2026) · Track: **Indie Developer** · Theme: **Build for Your World**

---

## The problem

During surgery, when a nurse needs an item, they call or message the ORMC (Operating Room Materials Core) on a VoLTE phone. Then:

- The one associate they reach may be busy, away, or covering several jobs.
- There are thousands of items, and surgical teams often use different names for the same one.
- If the associate doesn't recognize the name, they search the inventory app by hand, or need the item number.

Every minute spent on the phone is a minute lost in the operating room.

## The solution

1. The nurse opens the web app on the VoLTE phone and **types or speaks** the item name, using whatever name they know.
2. An **AI agent powered by a Meta model** works out which item they mean, checks stock, and shows the item's **photo, item number and nearest locations**: the same OR, the closest core, or the ORMC.
3. The nurse confirms the item and quantity and taps **Submit**.
4. **Every associate in the core is alerted at once** with the item, quantity, pick location and destination OR. The first to accept brings it.

No phone call, no misheard names, and no single point of failure.

## What it is not

This is a **supply logistics tool**. It does not give medical advice and never suggests which item to use. The surgical team decides what they need; the app only finds it and gets it delivered.

## How the agent works

The Meta model is not a simple search box. It runs as an agent with tools:

| Tool | What it does |
|---|---|
| `find_item` | Matches nicknames, misspellings and voice input to catalog items |
| `check_stock` | Looks up quantity at each location |
| `nearest_location` | Ranks locations by distance from the requesting OR |
| `dispatch_request` | Alerts all associates in the core and tracks Accepted / Delivered |

## Works with any inventory system

Hospitals run different inventory systems (Epic, Lawson/Infor, PAR Excellence, Omnicell, custom SQL databases). The app and the agent never talk to a system directly. They use one standard interface, and each system plugs in through a small **adapter**:

```
 Nurse app ─┐                        ┌─ JSON adapter    (demo data)
            ├─► Agent ─► Inventory ──┼─ CSV adapter     (any system's export)
Associate ──┘          interface     ├─ SQL adapter     (any SQL database, queries set in config)
 app                                 └─ Epic / FHIR     (template for hospital IT)
```

The interface has three calls: `list_items`, `list_locations` and `get_stock`. Connecting a new system means writing one file in `backend/app/inventory/` and setting `INVENTORY_SOURCE`. The tests check that every adapter returns the same data.

## Run it locally

```bash
pip install -r requirements-dev.txt
python data/generate_catalog.py        # rebuild the made-up catalog (optional)
uvicorn app.main:app --app-dir backend --reload
# open http://localhost:8000
pytest                                  # run the tests
```

## Project structure

```
backend/app/main.py            API
backend/app/inventory/         adapter interface and adapters
data/generate_catalog.py       builds the made-up catalog
data/catalog.json              291 items, 15 locations, stock levels
frontend/                      web app for nurses and associates
tests/                         automated tests
```

## Roadmap (built during the hackathon)

All code, data and assets in this repo were created during the event. Each day's work is in the commit history.

- [x] **Day 1, Oct 30:** README, roadmap, project setup, inventory adapter layer (JSON, CSV, SQL, Epic template), made-up catalog of 291 surgical items with nicknames and stock by location
- [ ] **Day 2, Oct 31:** Item search with typed input and the agent's `find_item` tool
- [ ] **Day 3, Nov 1:** Voice input, stock lookup and nearest-location ranking
- [ ] **Day 4, Nov 2:** Nurse screen: confirm item, photo and quantity, then submit
- [ ] **Day 5, Nov 3:** Associate screen with live alerts, Accept and Delivered; deploy a live demo
- [ ] **Day 6, Nov 4:** 3 minute demo video, final polish, submission

## Data and rights

All inventory data is **made up for this demo**. No real hospital or patient data is used. Images are created for this project or used under a license that allows it, with credits listed below.

## Credits

- Meta AI models: _to be added_
- Image credits: _to be added_

## License

MIT, see [LICENSE](LICENSE).
