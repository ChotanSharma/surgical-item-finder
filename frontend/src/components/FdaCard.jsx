// A real product from the FDA device database that we don't stock
function RecallBadge({ device }) {
  if (!device.recalls_checked) return <span className="stock muted">Recalls not checked</span>;
  const count = device.recalls.length;
  if (count === 0) return <span className="stock in">No recalls on record</span>;
  const latest = device.recalls[0];
  return (
    <span className="stock out" title={latest.reason || ""}>
      ⚠ {count} recall{count > 1 ? "s" : ""} · {latest.status} {latest.date?.slice(0, 4)}
    </span>
  );
}

export default function FdaCard({ device, onSource, sending }) {
  return (
    <li className="card fda-card">
      <div className="card-body">
        <div className="name">{device.description}</div>
        <div className="number">
          {device.company}
          {device.model_number && ` · model ${device.model_number}`}
        </div>
        <div className="badges">
          <span className={device.in_distribution ? "stock in" : "stock muted"}>
            {device.in_distribution ? "✓ Still sold" : "Discontinued"}
          </span>
          <RecallBadge device={device} />
        </div>
        <button className="secondary source" onClick={onSource} disabled={sending}>
          Ask ORMC to source this
        </button>
      </div>
    </li>
  );
}
