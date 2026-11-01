import { useState } from "react";

export default function SearchForm({ onSearch, disabled }) {
  const [query, setQuery] = useState("");

  function handleSubmit(event) {
    event.preventDefault(); // stop the browser from reloading the page
    const trimmed = query.trim();
    if (trimmed) onSearch(trimmed);
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="What do you need?"
        autoComplete="off"
      />
      <button type="submit" disabled={disabled}>
        Find
      </button>
    </form>
  );
}
