# Surgical Item Finder

**An AI agent that gets the right surgical supply to the operating room, without a phone call.**

Built solo for the **Meta Global AI Developer Hackathon** (Oct 26 to Nov 4, 2026) · Track: **Indie Developer** · Theme: **Build for Your World**

### Live demo: https://surgical-item-finder.onrender.com

> Free hosting: if the site has been idle, the first visit takes about a minute to wake up.

---

## The problem

During surgery, when a nurse needs an item, they call or message the ORMC (Operating Room Materials Core) on a VoLTE phone. Then:

- The one associate they reach may be busy, away, or covering several jobs.
- There are thousands of items, and surgical teams often use different names for the same one.
- If the associate doesn't recognize the name, they search the inventory app by hand, or need the item number.

Every minute spent on the phone is a minute lost in the operating room.

## The solution

1. The nurse picks their OR, then **types or speaks** the item name, using whatever name they know: "bovie", "lap sponge", or a misheard "Bobby".
2. A **Muse Spark agent** works out which item they mean and shows a **packaging-style photo**, the item number, and **where it's in stock**, ranked from nearest: the same OR, the OR's core, the ORMC, then other ORs.
3. The nurse adds items to a **cart**, sets quantities, reviews, and chooses:
   - **Deliver from ORMC:** every ORMC associate's screen **beeps at once**. The first to tap **Accept** gets it; others see it's taken.
   - **I'll pick it myself:** no alert, just a pick list with locations. The request is still recorded.
4. The nurse's screen updates live: **Sent → Maria is on the way → Delivered ✓**.

No phone call, no misheard names, and no single point of failure.

## Try it in 2 minutes

1. **Nurse** (phone or browser): open the [live demo](https://surgical-item-finder.onrender.com), choose an OR, and search **"Bobby"** or tap 🎤 and say it. The agent asks which type of bovie you mean.
2. Add one or two items to the cart, then tap **Deliver from ORMC → Confirm**.
3. **ORMC associate** (a second window or device): open [/ormc](https://surgical-item-finder.onrender.com/ormc), enter a name, and tap **Start shift**. The request appears with a beep.
4. Tap **Accept**, then **Delivered**, and watch the nurse's screen update.

Tip: open `/ormc` in two windows with different names (use a private window for the second) to see "first to accept wins".

## What it is not

This is a **supply logistics tool**. It does not give medical advice and never suggests which item to use. The surgical team decides what they need; the app only finds it and gets it delivered. The agent's instructions forbid clinical advice.

## How the agent works

Muse Spark 1.3 runs as a **tool-calling agent** (via the OpenAI-compatible Meta Model API):

| Tool | What it does |
|---|---|
| `find_item` | Searches the catalog by name, nickname, item number or manufacturer part number. The agent can call it several times with different wording, e.g. after spelling out what a nickname or misheard word likely means |
| `answer` | Ends the turn with one of: **match**, **clarify** (asks which one, e.g. 5 kinds of bovie), or **not found** |

Guard rails:
- **No made-up items:** every item number the model returns is checked against the catalog, and anything it didn't actually find is dropped.
- **Step limit:** at most 4 model calls per search.
- **Always works:** if the model is slow, errors, or isn't configured, the app falls back to plain search, so a nurse is never stuck.

After the agent picks the item, regular code handles the rest: **stock ranking** (enough stock first, then distance from the nurse's OR), **requests** stored in SQLite, and **first-to-accept** enforced by a single conditional database update, so two associates can't both win.

**Muse Image 1.0** generated the item photos in a packaging style, so ORMC associates without clinical training can spot the right box on the shelf.

## Tech

| Part | Built with |
|---|---|
| AI | Muse Spark 1.3 (agent), Muse Image 1.0 (photos), Meta Model API |
| Backend | Python, FastAPI, Pydantic, SQLite |
| Frontend | React 18, Vite, browser speech recognition, Web Audio alerts |
| Hosting | Docker on Render |
| Tests | pytest, 82 tests (models, search, agent with a fake model, stock ranking, requests, API) |

The inventory sits behind an `InventoryAdapter` interface, so a real hospital system could replace the demo JSON catalog without touching the agent or the screens.

## Run it locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env            # then put your Meta Model API key in .env
cd frontend && npm install && npm run build && cd ..
uvicorn app.main:app --app-dir backend --reload
```

Open http://localhost:8000 (nurse) and http://localhost:8000/ormc (associate). Run tests with `pytest`.

## Roadmap (built during the hackathon)

All code, data and assets in this repo were created during the event. Each day's work is in the commit history.

- [x] **Day 1, Oct 30:** README, roadmap, project setup, made-up catalog of 286 surgical items with nicknames and stock across 15 locations
- [x] **Day 2, Oct 31:** Item search and the Muse Spark agent with the `find_item` tool
- [x] **Day 3, Nov 1:** Voice input, stock lookup and nearest-location ranking
- [x] **Day 4, Nov 2:** Nurse screen: item photos, cart, review and submit
- [x] **Day 5, Nov 3:** ORMC screen with live alerts, Accept and Delivered; live status for the nurse; deployed live demo
- [x] **Day 6, Nov 4:** Demo video, final polish, submission
- [ ] **Next:** Muse supply insights: use the history of every request (delivered or self-picked) to flag high-use items and suggest restocking before they run out

## Data and rights

All inventory data is **made up for this demo**. No real hospital or patient data is used. All item images were generated for this project with Muse Image 1.0.

## Credits

- Meta AI models: Muse Spark 1.3 (agent) and Muse Image 1.0 (item photos), via the Meta Model API

## License

MIT, see [LICENSE](LICENSE).
