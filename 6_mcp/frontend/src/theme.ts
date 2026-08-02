// Light/dark theme. The choice is a data-theme attribute on <html>; the CSS
// reacts through its :root[data-theme="..."] blocks. Persisted in localStorage.

const KEY = "trading-floor-theme";
type Theme = "dark" | "light";

function apply(theme: Theme): void {
  document.documentElement.dataset.theme = theme;
  window.dispatchEvent(new Event("themechange"));
}

export function initTheme(button: HTMLButtonElement): void {
  const saved = (localStorage.getItem(KEY) as Theme | null) ?? "dark";
  apply(saved);
  button.addEventListener("click", () => {
    const next: Theme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    apply(next);
    localStorage.setItem(KEY, next);
  });
}
