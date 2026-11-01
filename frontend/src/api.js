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
