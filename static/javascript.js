// meme generator - config
function readPageConfig() {
  const conf = document.getElementById("meme-config");
  if (!conf) return null;
  const templates = (conf.dataset.templates || "").split(/[ ,]+/).filter(Boolean);
  const top = conf.dataset.top;
  const bottom = conf.dataset.bottom;
  return { templates, top, bottom };
}

// zufälliges meme template wählen
const meme_picker = (arr) => arr[(Math.random() * arr.length) | 0];
const buildMemeUrl = (cfg) =>
  `https://api.memegen.link/images/${meme_picker(cfg.templates)}/${encodeURIComponent(cfg.top)}/${encodeURIComponent(cfg.bottom)}.jpg`;

document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("form[id]");
  const cfg = readPageConfig();
  if (!form || !cfg) return;

  // Beim Seitenaufruf ein Meme vorladen
  let preload_url = buildMemeUrl(cfg);
  new Image().src = preload_url;

  // Klick-Handler
  form.addEventListener("click", (e) => {
    const btn = e.target.closest("button");
    if (!btn) return;

    // nicht sofort weiterleiten
    e.preventDefault();

    const img = document.getElementById("meme-img");
    const response = document.getElementById("response");
    if (!img || !response) return;

    // bereits vorgeladenes Meme anzeigen
    const meme_url = preload_url;

    // Meme für die nächste Seite vorladen
    preload_url = buildMemeUrl(cfg);
    new Image().src = preload_url;

      response.style.display = "block";
      img.onload = () => {
        setTimeout(() => {
          form.requestSubmit(btn);
        }, 2000);
      };
    img.onerror = () => console.warn("Meme could not load:", meme_url);
    img.src = meme_url;
  });
});

// Checkbox "all" Genres - deaktiviert alle anderen
document.addEventListener("DOMContentLoaded", () => {
  const all = document.getElementById("genre_all");
  const others = document.querySelectorAll('input[name="genres"]:not(#genre_all)');
  const skip = document.getElementById("skipGenres");

  if (!all) return;

  all.addEventListener("change", () => all.checked && others.forEach(g => g.checked = false));
  others.forEach(g => g.addEventListener("change", () => all.checked = false));
  if (skip) skip.addEventListener("click", () => all.checked = true);
});

// Checkbox "all" Languages - deaktiviert alle anderen
document.addEventListener("DOMContentLoaded", () => {
  const all = document.getElementById("lang_all");
  const others = document.querySelectorAll('input[name="languages"]:not(#lang_all)');
  const skip = document.getElementById("skipLangs");

  if (!all) return;

  all.addEventListener("change", () => all.checked && others.forEach(l => l.checked = false));
  others.forEach(l => l.addEventListener("change", () => all.checked = false));
  if (skip) skip.addEventListener("click", () => all.checked = true);
});
