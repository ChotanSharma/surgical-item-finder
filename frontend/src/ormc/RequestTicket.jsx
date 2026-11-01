import ItemPhoto from "../components/ItemPhoto.jsx";

function minutesAgo(createdAt) {
  const minutes = Math.floor((Date.now() - new Date(createdAt).getTime()) / 60000);
  return minutes < 1 ? "just now" : `${minutes} min ago`;
}

// One request as an ORMC associate sees it: where it goes, what to pick, where from
export default function RequestTicket({ request, actionLabel, onAction, busy, faded }) {
  return (
    <article className={faded ? "ticket faded" : `ticket ${request.status}`}>
      <div className="ticket-head">
        <span className="ticket-or">{request.or_id}</span>
        <span className="sub">
          #{request.id} · {minutesAgo(request.created_at)}
          {request.handled_by && ` · ${request.handled_by}`}
        </span>
      </div>

      <ul className="results">
        {request.lines.map((line) => (
          <li key={line.item_number} className="card">
            <ItemPhoto item={{ item_number: line.item_number, name: line.name, category: line.name }} />
            <div className="card-body">
              <div className="name">
                {line.quantity} × {line.name}
              </div>
              <div className="number">
                {line.item_number} · {line.pick_from_name ? `Pick from ${line.pick_from_name}` : "Check ORMC stock"}
              </div>
            </div>
          </li>
        ))}
      </ul>

      {onAction && (
        <button className="ticket-action" onClick={onAction} disabled={busy}>
          {busy ? "..." : actionLabel}
        </button>
      )}
    </article>
  );
}
