import CartLine from "./CartLine.jsx";

// Jump back to the search box, ready to type the next item
function searchAgain() {
  const input = document.getElementById("search");
  if (!input) return;
  input.scrollIntoView({ behavior: "smooth", block: "center" });
  input.focus({ preventScroll: true });
}

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
      <button className="add-more" onClick={searchAgain} disabled={sending}>
        <span className="add-more-icon" aria-hidden="true">+</span>
        <span className="add-more-text">
          <strong>Add another item</strong>
          <small>Type or say the next one</small>
        </span>
      </button>

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
