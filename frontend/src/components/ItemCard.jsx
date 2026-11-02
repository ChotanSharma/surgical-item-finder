import ItemPhoto from "./ItemPhoto.jsx";

export default function ItemCard({ item, inCart, onAdd }) {
  const total = item.stock.reduce((sum, s) => sum + s.quantity, 0);

  return (
    <li className="card">
      <ItemPhoto item={item} />
      <div className="card-body">
        <div className="name">{item.name}</div>
        <div className="number">
          {item.item_number} · {item.unit}
        </div>
                <div className="tags">
          {item.nicknames.slice(0, 3).map((nickname) => (
            <span key={nickname} className="tag">
              {nickname}
            </span>
          ))}
        </div>
        <div className={total > 0 ? "stock in" : "stock out"}>
          {total > 0 ? `${total} in stock` : "Out of stock"}
        </div>
      </div>
      <button className="add" onClick={onAdd} disabled={inCart || total === 0}>
        {inCart ? "In cart ✓" : "+ Add"}
      </button>
    </li>
  );
}
