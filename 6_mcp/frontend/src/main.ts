// App entry point: build a panel per trader, then poll the backend for portfolio
// data and activity logs. The trading floor runs on its own; this only reads.

import { getMarket, getTrader, getTraderLogs, getTraders } from "./api";
import { TraderPanel } from "./panel";
import { TraderState } from "./state";
import { initTheme } from "./theme";

const DATA_POLL_MS = 6000;
const LOG_POLL_MS = 2000;

initTheme(document.getElementById("btn-theme") as HTMLButtonElement);

const panelHost = document.getElementById("panels")!;
const states = new Map<string, TraderState>();
const panels = new Map<string, TraderPanel>();

async function loadMarket(): Promise<void> {
  try {
    const market = await getMarket();
    const badge = document.getElementById("market-badge")!;
    badge.dataset.source = market.source;
    document.getElementById("market-source")!.textContent =
      market.source === "massive" ? "Live market" : "Simulated";
    document.getElementById("market-status")!.textContent = market.is_market_open
      ? "Market open"
      : "Market closed";
  } catch (err) {
    console.error("market fetch failed", err);
  }
}

async function buildPanels(): Promise<void> {
  const traders = await getTraders();
  for (const info of traders) {
    const state = new TraderState(info);
    const panel = new TraderPanel(state);
    states.set(info.name, state);
    panels.set(info.name, panel);
    panelHost.append(panel.root);
    panel.mount();
  }
}

async function pollData(): Promise<void> {
  await Promise.all(
    [...states].map(async ([name, state]) => {
      try {
        state.recordDetail(await getTrader(name));
        panels.get(name)!.update();
      } catch (err) {
        console.error(`data fetch failed for ${name}`, err);
      }
    }),
  );
  markLeader();
  renderReturns();
}

function renderReturns(): void {
  const list = document.getElementById("returns-list")!;
  const rows = [...states.values()]
    .map((s) => s.detail)
    .filter((d): d is NonNullable<typeof d> => d !== null)
    .map((d) => {
      const initial = d.portfolio_value - d.pnl; // each trader started with this
      return { name: d.name, pct: initial > 0 ? (d.pnl / initial) * 100 : 0 };
    })
    .sort((a, b) => b.pct - a.pct);
  list.innerHTML = "";
  for (const r of rows) {
    const li = document.createElement("li");
    li.className = "returns-row";
    const name = document.createElement("span");
    name.className = "returns-name";
    name.textContent = r.name;
    const pct = document.createElement("span");
    pct.className = "returns-pct";
    pct.dataset.trend = r.pct >= 0 ? "up" : "down";
    pct.textContent = `${r.pct >= 0 ? "+" : ""}${r.pct.toFixed(1)}%`;
    li.append(name, pct);
    list.append(li);
  }
}

async function pollLogs(): Promise<void> {
  await Promise.all(
    [...panels].map(async ([name, panel]) => {
      try {
        panel.renderLogs(await getTraderLogs(name));
      } catch (err) {
        console.error(`log fetch failed for ${name}`, err);
      }
    }),
  );
}

function markLeader(): void {
  const values = [...states.values()].map((s) => s.detail?.portfolio_value).filter((v): v is number => v !== undefined);
  const best = Math.max(...values);
  // Only crown a single clear leader; a tie (e.g. before any trading) highlights nobody.
  const unique = values.filter((v) => v === best).length === 1;
  for (const [name, state] of states) {
    panels.get(name)!.setLeader(unique && state.detail?.portfolio_value === best);
  }
}

async function main(): Promise<void> {
  await loadMarket();
  await buildPanels();
  await pollData();
  await pollLogs();
  setInterval(pollData, DATA_POLL_MS);
  setInterval(pollLogs, LOG_POLL_MS);
}

main().catch((err) => console.error("startup failed", err));
