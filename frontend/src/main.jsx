import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import OrmcApp from "./ormc/OrmcApp.jsx";
import "./styles.css";

// One app, two screens: nurses use "/", ORMC associates use "/ormc"
const isOrmc = window.location.pathname.startsWith("/ormc");

createRoot(document.getElementById("root")).render(
  <StrictMode>{isOrmc ? <OrmcApp /> : <App />}</StrictMode>,
);
