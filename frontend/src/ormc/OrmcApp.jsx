import { useEffect, useRef, useState } from "react";
import { acceptRequest, deliverRequest, listRequests } from "../api.js";
import RequestTicket from "./RequestTicket.jsx";
import { alertNewRequest, unlockSound } from "./alert.js";

const POLL_MS = 2000; // check for new requests every 2 seconds

function loadName() {
  try {
    return localStorage.getItem("associate") || "";
  } catch {
    return "";
  }
}

function OrmcHeader({ line }) {
  return (
    <header className="appbar">
      <div className="brand">
        <span className="logo">+</span>
        <div>
          <h1>ORMC requests</h1>
          <div className="tagline">{line}</div>
        </div>
      </div>
    </header>
  );
}

export default function OrmcApp() {
  const [name, setName] = useState(loadName);
  const [onShift, setOnShift] = useState(false);
  const [requests, setRequests] = useState([]);
  const [error, setError] = useState(null);
  const [busyId, setBusyId] = useState(null);
  const seen = useRef(null); // ids already shown, so only new ones beep

  async function refresh() {
    try {
      const latest = await listRequests(["sent", "accepted"]);
      const waitingIds = latest.filter((r) => r.status === "sent").map((r) => r.id);
      if (seen.current && waitingIds.some((id) => !seen.current.has(id))) {
        alertNewRequest();
      }
      seen.current = new Set(latest.map((r) => r.id));
      setRequests(latest);
      setError(null);
    } catch (err) {
      setError(`Can't reach the server. ${err.message}`);
    }
  }

  // Start polling once the shift starts; stop when the screen closes
  useEffect(() => {
    if (!onShift) return;
    refresh();
    const timer = setInterval(refresh, POLL_MS);
    return () => clearInterval(timer);
  }, [onShift]);

  function startShift(event) {
    event.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;
    setName(trimmed);
    try {
      localStorage.setItem("associate", trimmed);
    } catch {
      // not saved, but the app still works
    }
    unlockSound(); // browsers only allow sound after a tap
    setOnShift(true);
  }

  async function act(action, request) {
    setBusyId(request.id);
    try {
      await action(request.id, name);
      setError(null);
    } catch (err) {
      setError(err.message); // e.g. "already accepted by Sam"
    } finally {
      setBusyId(null);
      refresh();
    }
  }

  if (!onShift) {
    return (
      <main>
        <OrmcHeader line="Materials core · start your shift" />
        <form onSubmit={startShift}>
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Your name"
            autoComplete="name"
          />
          <button type="submit">Start shift</button>
        </form>
        <p className="sub">New requests will beep and appear here instantly.</p>
      </main>
    );
  }

  const waiting = requests.filter((r) => r.status === "sent");
  const mine = requests.filter((r) => r.status === "accepted" && r.handled_by === name);
  const others = requests.filter((r) => r.status === "accepted" && r.handled_by !== name);

  return (
    <main>
     <OrmcHeader line={<span className="live">Live · on shift: {name}</span>} />
      {error && <p className="message not_found">{error}</p>}

      <h2 className="section">On my way ({mine.length})</h2>
      {mine.length === 0 && <p className="sub">Nothing accepted yet.</p>}
      {mine.map((r) => (
        <RequestTicket key={r.id} request={r} busy={busyId === r.id}
          actionLabel="Delivered" onAction={() => act(deliverRequest, r)} />
      ))}

      <h2 className="section">Waiting ({waiting.length})</h2>
      {waiting.length === 0 && <p className="sub">All caught up.</p>}
      {waiting.map((r) => (
        <RequestTicket key={r.id} request={r} busy={busyId === r.id}
          actionLabel="Accept" onAction={() => act(acceptRequest, r)} />
      ))}

      {others.length > 0 && (
        <>
          <h2 className="section">Taken by others ({others.length})</h2>
          {others.map((r) => (
            <RequestTicket key={r.id} request={r} faded />
          ))}
        </>
      )}
    </main>
  );
}
