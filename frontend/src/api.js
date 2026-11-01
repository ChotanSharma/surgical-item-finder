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


// ---- ORMC side ----

// Like fetch, but turns the server's error message ("already accepted by Sam") into the Error text
async function call(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    let detail = `Server error ${response.status}`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // body wasn't JSON; keep the generic message
    }
    throw new Error(detail);
  }
  return response.json();
}

export function listRequests(statuses) {
  const params = new URLSearchParams();
  statuses.forEach((status) => params.append("status", status));
  return call(`/requests?${params}`);
}

export function getRequest(requestId) {
  return call(`/requests/${requestId}`);
}

function postAs(url, associate) {
  return call(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ associate }),
  });
}

export function acceptRequest(requestId, associate) {
  return postAs(`/requests/${requestId}/accept`, associate);
}

export function deliverRequest(requestId, associate) {
  return postAs(`/requests/${requestId}/deliver`, associate);
}


