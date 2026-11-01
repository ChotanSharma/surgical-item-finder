import { useState } from "react";
import { findItem, sendRequest } from "./api.js";
import OrPicker from "./components/OrPicker.jsx";
import SearchForm from "./components/SearchForm.jsx";
import ItemCard from "./components/ItemCard.jsx";
import Cart from "./components/Cart.jsx";
import RequestConfirmation from "./components/RequestConfirmation.jsx";

const STATUS_TEXT = {
  match: "Found it",
  clarify: "Which one?",
  not_found: "Not found",
  fallback: "Search results",
};

function loadOr() {
  try {
    return localStorage.getItem("or_id") || "OR-01";
  } catch {
    return "OR-01"; // private mode or storage blocked
  }
}

export default function App() {
  const [orId, setOrId] = useState(loadOr);
  const [query, setQuery] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null);
  const [cart, setCart] = useState([]); // [{ item, quantity }]
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(null); // the saved request, after Send

  function changeOr(newOr) {
    setOrId(newOr);
    try {
      localStorage.setItem("or_id", newOr);
    } catch {
      // not saved, but the app still works
    }
  }

  async function handleSearch(text = query) {
    const trimmed = text.trim();
    if (!trimmed) return;
    setLoading(true);
    setError(null);
    setNotice(null);
    setResult(null);
    try {
      setResult(await findItem(trimmed));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleVoice(text) {
    setQuery(text); // show what was heard, so the nurse can check it
    handleSearch(text);
  }

  function addToCart(item) {
    setCart((current) => [...current, { item, quantity: 1 }]);
    setNotice(`Added: ${item.name}`);
    setQuery("");
    setResult(null);
  }

  function changeQuantity(itemNumber, quantity) {
    setCart((current) =>
      current.map((line) => (line.item.item_number === itemNumber ? { ...line, quantity } : line)),
    );
  }

  function removeFromCart(itemNumber) {
    setCart((current) => current.filter((line) => line.item.item_number !== itemNumber));
  }

   async function handleSend(fulfillment) {
    setSending(true);
    setError(null);
    try {
      setSent(await sendRequest(orId, fulfillment, cart));
      setCart([]);
      setNotice(null);
      setResult(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setSending(false);
    }
  }


  const inCart = new Set(cart.map((line) => line.item.item_number));
  
  if (sent) {
    return (
      <main>
        <RequestConfirmation request={sent} onDone={() => setSent(null)} />
      </main>
    );
  }

  return (
    <main>
      <header>
        <h1>Surgical Item Finder</h1>
        <OrPicker value={orId} onChange={changeOr} />
      </header>
      
      <SearchForm
        query={query}
        onQueryChange={setQuery}
        onSearch={() => handleSearch()}
        onVoice={handleVoice}
        onVoiceError={setError}
        disabled={loading}
      />

      {notice && <p className="message match">{notice} ✓</p>}
      {loading && <p className="message">Searching...</p>}
      {error && <p className="message not_found">Something went wrong. {error}</p>}

      {result && (
        <>
          <p className={`message ${result.status}`}>
            {STATUS_TEXT[result.status]}: {result.message}
          </p>
          <ul className="results">
            {result.items.map((item) => (
              <ItemCard
                key={item.item_number}
                item={item}
                inCart={inCart.has(item.item_number)}
                onAdd={() => addToCart(item)}
              />
            ))}
          </ul>
        </>
      )}

        <Cart
            lines={cart}
            orId={orId}
            onQuantityChange={changeQuantity}
            onRemove={removeFromCart}
            onSend={handleSend}
            sending={sending}
      />
    </main>
  );
}
