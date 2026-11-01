import { useState } from "react";
import { findItem } from "./api.js";
import SearchForm from "./components/SearchForm.jsx";
import ItemCard from "./components/ItemCard.jsx";

const STATUS_TEXT = {
  match: "Found it",
  clarify: "Which one?",
  not_found: "Not found",
  fallback: "Search results",
};

export default function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);

  async function handleSearch(query) {
    setLoading(true);
    setError(null);
    setResult(null);
    setSelected(null);
    try {
      setResult(await findItem(query));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <header>
        <h1>Surgical Item Finder</h1>
        <p className="sub">Type any name the team uses: "bovie", "laps", "vicryl 2-0"</p>
      </header>

      <SearchForm onSearch={handleSearch} disabled={loading} />

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
                selected={selected === item.item_number}
                onSelect={() => setSelected(item.item_number)}
              />
            ))}
          </ul>
        </>
      )}
    </main>
  );
}
