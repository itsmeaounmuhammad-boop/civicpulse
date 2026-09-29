import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "1m", target: 20 },   // ramp up
    { duration: "3m", target: 300 },  // sustained load — should trigger HPA
    { duration: "1m", target: 0 },    // ramp down
  ],
  thresholds: {
    http_req_failed: ["rate<0.05"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://civicpulse.local";

export default function () {
  const listRes = http.get(`${BASE_URL}/api/complaints?page=1&page_size=20`);
  check(listRes, { "list status is 200": (r) => r.status === 200 });

  const statsRes = http.get(`${BASE_URL}/api/stats`);
  check(statsRes, { "stats status is 200": (r) => r.status === 200 });

  sleep(1);
}