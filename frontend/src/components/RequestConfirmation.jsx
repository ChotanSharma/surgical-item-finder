import { useEffect, useState } from "react";
import { getRequest } from "../api.js";

const POLL_MS = 2000; // same pace as the ORMC screen
const STEPS = ["sent", "accepted", "delivered"];

function stepText(step, request) {
  if (step === "sent") return "Sent to ORMC";
  if (step === "accepted") {
    return request.handled_by ? `${request.handled_by} is on the way` : "Waiting for an associate";
  }
  return "Delivered";
}

export default function RequestConfirmation({ request: first, onDone }) {
  const [request, setRequest] = useState(first);
  const [offline, setOffline] = useState(false);
  const delivery = request.fulfillment === "ormc_delivery";
  const finished = !delivery || request.status === "delivered";

  // Ask the server for the latest status every 2 seconds until it's delivered
  useEffect(() => {
    if (finished) return;
    const timer = setInterval(async () => {
      try {
        setRequest(await getRequest(first.id));
        setOffline(false);
      } catch {
        setOffline(true); // keep trying; Wi-Fi in the OR can drop
      }
    }, POLL_MS);
    return () => clearInterval(timer);
  }, [first.id, finished]);

  const reached = STEPS.indexOf(request.status); // how far along it is

  return (
    <section className={`confirmation ${request.status}`}>
      <h2>
        {delivery ? `Request #${request.id} for ${request.or_id}` : `Pick list #${request.id} saved`}
      </h2>

      {delivery ? (
        <ol className="tracker">
          {STEPS.map((step, index) => (
            <li key={step} className={index <= reached ? "done" : ""}>
              {index <= reached ? "✓ " : ""}
              {stepText(step, request)}
            </li>
          ))}
        </ol>
      ) : (
        <p className="sub">Pick these up yourself:</p>
      )}

      {offline && <p className="sub">Reconnecting...</p>}

      <ul className="pick-list">
        {request.lines.map((line) => (
          <li key={line.item_number}>
            <strong>{line.quantity} ×</strong> {line.name}
            <div className="number">
              {line.pick_from_name ? `From ${line.pick_from_name}` : "Not enough stock nearby"}
            </div>
          </li>
        ))}
      </ul>
      <button onClick={onDone}>New request</button>
    </section>
  );
}

