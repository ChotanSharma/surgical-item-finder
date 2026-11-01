export default function SearchForm({ query, onQueryChange, onSearch, disabled }) {
  function handleSubmit(event) {
    event.preventDefault(); // stop the browser from reloading the page
    onSearch();
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="search"
        value={query}
        onChange={(event) => onQueryChange(event.target.value)}
        placeholder='What do you need? e.g. "bovie"'
        autoComplete="off"
      />
      <button type="submit" disabled={disabled}>
        Find
      </button>
    </form>
  );
}
