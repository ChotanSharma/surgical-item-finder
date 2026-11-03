import { useState } from "react";
import { findItem, sendRequest, sourceRequest } from "./api.js";
import FdaCard from "./components/FdaCard.jsx";
import OrPicker from "./components/OrPicker.jsx";
import SearchForm from "./components/SearchForm.jsx";
import ItemCard from "./components/ItemCard.jsx";
import Cart from "./components/Cart.jsx";
import RequestConfirmation from "./components/RequestConfirmation.jsx";
import ReviewRequest from "./components/ReviewRequest.jsx";

const EXAMPLES = ["bovie", "Bobby", "lap sponge", "yankauer"]; // tap to try

const STATUS_TEXT = {
  match: "Found it",
  clarify: "Which one?",
  not_found: "Not found",
  fallback: "Search results",
  not_in_catalog: "Not stocked here",

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
  const [reviewing, setReviewing] = useState(null); // "ormc_delivery" or "self_pick" while confirming

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
      setReviewing(null);
      setCart([]);
      setNotice(null);
      setResult(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setSending(false);
    }
  }

  
  // Not stocked here: send ORMC a request to get it from a supplier
  async function handleSource(device) {
    if (!window.confirm(`Ask ORMC to source "${device.description}" for ${orId}?`)) return;
    setSending(true);
    setError(null);
    try {
      setSent(await sourceRequest(orId, device));
      setResult(null);
      setQuery("");
    } catch (err) {
      setError(err.message);
    } finally {
      setSending(false);
    }
  }

  const inCart = new Set(cart.map((line) => line.item.item_number));
  
    if (reviewing) {
    return (
      <main>
        <ReviewRequest
          lines={cart}
          orId={orId}
          fulfillment={reviewing}
          onConfirm={() => handleSend(reviewing)}
          onBack={() => {
            setReviewing(null);
            setError(null);
          }}
          sending={sending}
          error={error}
        />
      </main>
    );
  }


  if (sent) {
    return (
      <main>
        <RequestConfirmation request={sent} onDone={() => setSent(null)} />
      </main>
    );
  }

  return (
    <main>
            <header className="appbar">
        <div className="brand">
          <span className="logo">+</span>
          <div>
            <h1>Surgical Item Finder</h1>
            <div className="tagline">Find it. Send it. No phone call.</div>
          </div>
        </div>
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
            {!result && !loading && !error && cart.length === 0 && (
        <section className="hint">
          <p>Try saying or tapping:</p>
          <div className="chips">
            {EXAMPLES.map((text) => (
              <button key={text} className="chip" onClick={() => handleVoice(text)}>
                {text}
              </button>
            ))}
          </div>
        </section>
      )}
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
          {result.fda_devices?.length > 0 && (
            <>
              <h2 className="section">Similar products listed with the FDA</h2>
              <p className="sub">Not in our inventory. ORMC can source one from the maker or a supplier.</p>
              <ul className="results">
                {result.fda_devices.map((device, index) => (
                  <FdaCard
                    key={`${device.company}-${device.model_number}-${index}`}
                    device={device}
                    onSource={() => handleSource(device)}
                    sending={sending}
                  />
                ))}
              </ul>
            </>
          )}
        </>
      )}

        <Cart
            lines={cart}
            orId={orId}
            onQuantityChange={changeQuantity}
            onRemove={removeFromCart}
            onSend={setReviewing}
            sending={sending}
      />
    </main>
  );
}
