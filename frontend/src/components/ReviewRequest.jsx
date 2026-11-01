import ItemPhoto from "./ItemPhoto.jsx";

// Last check before anything is sent: big, clear, and one tap to go back
export default function ReviewRequest({ lines, orId, fulfillment, onConfirm, onBack, sending, error }) {
  const delivery = fulfillment === "ormc_delivery";
  const units = lines.reduce((sum, line) => sum + line.quantity, 0);

  return (
    <section className="review">
      <h2>{delivery ? `Deliver to ${orId}?` : `Pick up yourself for ${orId}?`}</h2>
      <p className="sub">
        {lines.length} item{lines.length > 1 ? "s" : ""}, {units} unit{units > 1 ? "s" : ""}.{" "}
        {delivery ? "Every ORMC associate will be alerted." : "Nothing is sent to ORMC; the pick is recorded."}
      </p>

      <ul className="results">
        {lines.map(({ item, quantity }) => (
          <li key={item.item_number} className="card">
            <ItemPhoto item={item} />
            <div className="card-body">
              <div className="name">{item.name}</div>
              <div className="number">
                {item.item_number} · {item.unit}
              </div>
            </div>
            <div className="review-qty">× {quantity}</div>
          </li>
        ))}
      </ul>

      {error && <p className="message not_found">Not sent. {error}</p>}

      <div className="send">
        <button className="secondary" onClick={onBack} disabled={sending}>
          Back
        </button>
        <button onClick={onConfirm} disabled={sending}>
          {sending ? "Sending..." : delivery ? "Confirm and send" : "Confirm pick list"}
        </button>
      </div>
    </section>
  );
}
