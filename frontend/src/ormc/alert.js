// A short double beep plus a vibration when a new request arrives.
// Browsers block sound until the user taps something, so unlockSound()
// runs on the "Start shift" tap.

let audio = null;

export function unlockSound() {
  const AudioContext = window.AudioContext || window.webkitAudioContext;
  if (AudioContext && !audio) audio = new AudioContext();
}

function beep(startAt) {
  const tone = audio.createOscillator();
  const volume = audio.createGain();
  tone.frequency.value = 880; // a clear, high note
  volume.gain.setValueAtTime(0.3, startAt);
  volume.gain.exponentialRampToValueAtTime(0.001, startAt + 0.25);
  tone.connect(volume).connect(audio.destination);
  tone.start(startAt);
  tone.stop(startAt + 0.25);
}

export function alertNewRequest() {
  if (audio) {
    beep(audio.currentTime);
    beep(audio.currentTime + 0.35);
  }
  navigator.vibrate?.([200, 100, 200]); // phones only; ignored elsewhere
}
