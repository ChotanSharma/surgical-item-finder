import CartLine from "./CartLine.jsx";

export default function Cart({ lines, orId, onQuantityChange, onRemove }) {
  if (lines.length === 0) return null;

  return (
    <section className="cart">
      <h2>Cart ({lines.length})</h2>
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
    </section>
  );
}
