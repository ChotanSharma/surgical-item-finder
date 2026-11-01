const ORS = Array.from({ length: 12 }, (_, i) => `OR-${String(i + 1).padStart(2, "0")}`);

export default function OrPicker({ value, onChange }) {
  return (
    <label className="or-picker">
      I'm in
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {ORS.map((or) => (
          <option key={or} value={or}>
            {or}
          </option>
        ))}
      </select>
    </label>
  );
}
