import CartLine from "./CartLine.jsx";

export default function Cart({ lines, orId, onQuantityChange, onRemove, onSend, sending }) {
  if (lines.length === 0) return null;

  return (
    <section className="cart">
      <h2>
        Cart <span className="count">{lines.length}</span>
      </h2>
      <ul className="results">
        {lines.map((line) => (
          <CartLine
            key={line.item.item_number}
            line={line}
            orId={orId}
            onQuantityChange={(quantity) => onQuantityChange(line.item.item_number, quantity)}
            onRemove={() => onRemove(line.item.item_number)}
          />
        ))}
      </ul>
      <div className="send">
        <button onClick={() => onSend("ormc_delivery")} disabled={sending}>
          Deliver from ORMC
        </button>
        <button className="secondary" onClick={() => onSend("self_pick")} disabled={sending}>
          I'll pick it myself
        </button>
      </div>
    </section>
  );
}
