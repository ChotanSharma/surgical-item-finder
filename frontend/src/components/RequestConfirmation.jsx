export default function RequestConfirmation({ request, onDone }) {
  const delivered = request.fulfillment === "ormc_delivery";

  return (
    <section className="confirmation">
      <h2>
        {delivered
          ? `Request #${request.id} sent to ORMC`
          : `Pick list #${request.id} saved`}
      </h2>
      <p className="sub">
        {delivered
          ? `An associate will bring it to ${request.or_id}.`
          : "Pick these up yourself:"}
      </p>
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
