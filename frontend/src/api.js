// All calls to the FastAPI backend live here.

export async function findItem(query) {
  const response = await fetch("/agent/find", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!response.ok) throw new Error(`Server error ${response.status}`);
  return response.json();
}

export async function getAvailability(itemNumber, orId, quantity) {
  const params = new URLSearchParams({ or_id: orId, quantity });
  const response = await fetch(`/items/${itemNumber}/availability?${params}`);
  if (!response.ok) throw new Error(`Server error ${response.status}`);
  return response.json();
}


export async function sendRequest(orId, fulfillment, cart) {
  const response = await fetch("/requests", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      or_id: orId,
      fulfillment,
      lines: cart.map((line) => ({ item_number: line.item.item_number, quantity: line.quantity })),
    }),
  });
  if (!response.ok) throw new Error(`Server error ${response.status}`);
  return response.json();
}

