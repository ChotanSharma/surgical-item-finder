import { useState } from "react";

// Shows /images/<item number>.webp, or a plain placeholder if there's no photo yet
export default function ItemPhoto({ item }) {
  const [missing, setMissing] = useState(false);

  if (missing) return <div className="photo placeholder">{item.category.slice(0, 1)}</div>;

  return (
    <img
      className="photo"
      src={`/images/${item.item_number}.webp`}
      alt={item.name}
      loading="lazy"
      onError={() => setMissing(true)}
    />
  );
}
