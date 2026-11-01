import { useEffect, useState } from "react";
import { getAvailability } from "../api.js";

export default function CartLine({ line, orId, onQuantityChange, onRemove }) {
  const { item, quantity } = line;
  const [places, setPlaces] = useState(null); // null = still loading

  // Ask the backend where to get it whenever the item, OR or quantity changes
  useEffect(() => {
    let current = true; // ignore answers that arrive after a newer request
    setPlaces(null);
    getAvailability(item.item_number, orId, quantity)
      .then((data) => current && setPlaces(data))
      .catch(() => current && setPlaces([]));
    return () => {
      current = false;
    };
  }, [item.item_number, orId, quantity]);

  const best = places?.[0];

  return (
    <li className="card cart-line">
      <div className="card-body">
        <div className="name">{item.name}</div>
        <div className="number">
          {item.item_number} · {item.unit}
        </div>
        <div className="where">
          {places === null && "Checking stock..."}
          {places?.length === 0 && <span className="stock out">Not in stock anywhere</span>}
          {best && (
            <span className={best.enough ? "stock in" : "stock out"}>
              Get from {best.location.name} · {best.walk_minutes} min · {best.quantity} there
              {!best.enough && " (not enough)"}
            </span>
          )}
        </div>
      </div>
      <div className="qty">
        <button onClick={() => (quantity > 1 ? onQuantityChange(quantity - 1) : onRemove())}>
          {quantity > 1 ? "−" : "✕"}
        </button>
        <span>{quantity}</span>
        <button onClick={() => onQuantityChange(quantity + 1)}>+</button>
      </div>
    </li>
  );
}
