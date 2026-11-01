import { useRef, useState } from "react";

// Chrome, Edge and Safari have speech recognition built in (some with a "webkit" prefix)
const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;

export default function VoiceButton({ onResult, onError, disabled }) {
  const [listening, setListening] = useState(false);
  const recognizer = useRef(null);

  if (!Recognition) return null; // no speech support in this browser: typing still works

  function start() {
    const r = new Recognition();
    r.lang = "en-US";
    r.interimResults = false;
    r.maxAlternatives = 1;
    r.onresult = (event) => onResult(event.results[0][0].transcript);
    r.onerror = (event) =>
      onError(event.error === "not-allowed" ? "Microphone is blocked. Allow it in the browser." : "Didn't catch that. Try again.");
    r.onend = () => setListening(false);
    recognizer.current = r;
    r.start();
    setListening(true);
  }

  function stop() {
    recognizer.current?.stop();
  }

  return (
    <button
      type="button"
      className={listening ? "mic listening" : "mic"}
      onClick={listening ? stop : start}
      disabled={disabled}
      aria-label={listening ? "Stop listening" : "Say the item name"}
    >
      {listening ? "■" : "🎤"}
    </button>
  );
}
