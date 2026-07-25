// The per-trader activity log. Rows come from the backend already coloured by
// type (the same custom-tracing colours as the Gradio dashboard).

import type { LogRow } from "./api";

export class LogView {
  private host: HTMLElement;

  constructor(host: HTMLElement) {
    this.host = host;
    host.classList.add("log");
  }

  render(rows: LogRow[]): void {
    this.host.innerHTML = "";
    if (rows.length === 0) {
      const empty = document.createElement("div");
      empty.className = "log-empty";
      empty.textContent = "Waiting for activity";
      this.host.append(empty);
      return;
    }
    for (const row of rows) {
      const el = document.createElement("div");
      el.className = "log-row";

      const time = document.createElement("span");
      time.className = "log-time";
      time.textContent = timeOf(row.datetime);

      const type = document.createElement("span");
      type.className = "log-type";
      type.style.color = row.color;
      type.textContent = row.type;

      const text = document.createElement("span");
      text.className = "log-text";
      text.textContent = row.message;

      el.append(time, type, text);
      this.host.append(el);
    }
    this.host.scrollTop = this.host.scrollHeight;
  }
}

function timeOf(stamp: string): string {
  // Stored as "YYYY-MM-DD HH:MM:SS"; show just the time.
  const parts = stamp.split(" ");
  return parts.length > 1 ? parts[1] : stamp;
}
