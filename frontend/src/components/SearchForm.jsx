import VoiceButton from "./VoiceButton.jsx";

export default function SearchForm({ query, onQueryChange, onSearch, onVoice, onVoiceError, disabled }) {
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
        placeholder='Type or say it, e.g. "bovie"'
        autoComplete="off"
      />
      <VoiceButton onResult={onVoice} onError={onVoiceError} disabled={disabled} />
      <button type="submit" disabled={disabled}>
        Find
      </button>
    </form>
  );
}
