/**
 * § PRE-PROD-STRESS t2: нагрузка read-only API (k6).
 *
 *   k6 run scripts/preprod_k6_feed.js
 *   k6 run -e API_URL=https://api.rawlead.ru scripts/preprod_k6_feed.js
 *
 * Порог S3: p95 feed < 2s, http_req_failed rate < 1%.
 */
import http from "k6/http";
import { check, sleep } from "k6";
import { Trend } from "k6/metrics";

const API_URL = (__ENV.API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const VUS = Number(__ENV.VUS || 50);
const DURATION = __ENV.DURATION || "5m";

const feedTrend = new Trend("feed_latency", true);
const catalogTrend = new Trend("catalog_latency", true);

export const options = {
  vus: VUS,
  duration: DURATION,
  thresholds: {
    http_req_failed: ["rate<0.01"],
    feed_latency: ["p(95)<2000"],
    http_req_duration: ["p(95)<3000"],
  },
};

const paths = [
  { name: "health", url: `${API_URL}/health` },
  { name: "feed", url: `${API_URL}/v1/feed?limit=20` },
  { name: "catalog", url: `${API_URL}/v1/skills/catalog` },
];

export default function () {
  for (const p of paths) {
    const res = http.get(p.url, { tags: { name: p.name } });
    check(res, {
      [`${p.name} status 200`]: (r) => r.status === 200,
    });
    if (p.name === "feed") {
      feedTrend.add(res.timings.duration);
    }
    if (p.name === "catalog") {
      catalogTrend.add(res.timings.duration);
    }
  }
  sleep(0.3);
}

export function handleSummary(data) {
  const p95Feed =
    data.metrics.feed_latency && data.metrics.feed_latency.values
      ? data.metrics.feed_latency.values["p(95)"]
      : null;
  const failRate =
    data.metrics.http_req_failed && data.metrics.http_req_failed.values
      ? data.metrics.http_req_failed.values.rate
      : null;
  const summary = {
    api_url: API_URL,
    vus: VUS,
    duration: DURATION,
    p95_feed_ms: p95Feed,
    http_req_failed_rate: failRate,
    s3_pass:
      p95Feed !== null &&
      p95Feed < 2000 &&
      failRate !== null &&
      failRate < 0.01,
  };
  return {
    stdout: JSON.stringify(summary, null, 2) + "\n",
    "data/preprod_k6_summary.json": JSON.stringify(summary, null, 2),
  };
}
