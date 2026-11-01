export default function ItemCard({ item, selected, onSelect }) {
  const total = item.stock.reduce((sum, s) => sum + s.quantity, 0);

  return (
    <li className={selected ? "card selected" : "card"} onClick={onSelect}>
      <div className="name">{item.name}</div>
      <div className="number">
        {item.item_number} · {item.unit}
      </div>
      <div className="nicknames">{item.nicknames.join(", ")}</div>
      <div className={total > 0 ? "stock in" : "stock out"}>
        {total > 0 ? `${total} in stock` : "Out of stock"}
      </div>
    </li>
  );
}
