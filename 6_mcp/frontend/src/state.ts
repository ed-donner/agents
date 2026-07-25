// Per-trader client state. The chart is seeded once from the stored time series,
// then grows a point on every poll so the line keeps moving while you watch.

import type { Holding, TraderDetail, TraderInfo } from "./api";

export const CHART_MAX_POINTS = 5000;

export interface ChartPoint {
  t: number; // unix seconds
  value: number;
}

function toUnixSeconds(stamp: string): number {
  // Stored timestamps are "YYYY-MM-DD HH:MM:SS" local time.
  return new Date(stamp.replace(" ", "T")).getTime() / 1000;
}

export class TraderState {
  readonly info: TraderInfo;
  detail: TraderDetail | null = null;
  chart: ChartPoint[] = [];
  previousPrices: Record<string, number> = {};
  private seeded = false;

  constructor(info: TraderInfo) {
    this.info = info;
  }

  recordDetail(detail: TraderDetail): void {
    this.detail = detail;
    if (!this.seeded) {
      this.chart = detail.time_series.map((p) => ({ t: toUnixSeconds(p.datetime), value: p.value }));
      this.seeded = true;
    }
    this.chart.push({ t: Date.now() / 1000, value: detail.portfolio_value });
    if (this.chart.length > CHART_MAX_POINTS) {
      this.chart.splice(0, this.chart.length - CHART_MAX_POINTS);
    }
  }

  priceDirections(): Record<string, "up" | "down" | "same"> {
    const out: Record<string, "up" | "down" | "same"> = {};
    if (!this.detail) return out;
    for (const h of this.detail.holdings) {
      const prev = this.previousPrices[h.symbol];
      out[h.symbol] =
        prev === undefined || prev === h.price ? "same" : h.price > prev ? "up" : "down";
    }
    return out;
  }

  rememberPrices(): void {
    if (!this.detail) return;
    this.previousPrices = Object.fromEntries(this.detail.holdings.map((h: Holding) => [h.symbol, h.price]));
  }
}
