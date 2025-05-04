import http from "k6/http";
import { check, sleep } from "k6";
import { Rate } from "k6/metrics";

let errorRate = new Rate("errors");

export let options = {
  vus: __ENV.VUS ? +__ENV.VUS : 50,
  duration: __ENV.DURATION || "1m",
  thresholds: {
    errors: ["rate<0.01"],
    http_req_duration: ["p(95)<1000"],
  },
};

const CHECKOUT_RATE = __ENV.CHECKOUT_RATE
  ? parseFloat(__ENV.CHECKOUT_RATE)
  : 0.1;

const BASE = "http://api.zamazon.local";

export function setup() {
  const email = __ENV.TEST_EMAIL || "perfuser@example.com";
  const password = __ENV.TEST_PASSWORD || "12345678";

  let loginRes = http.post(
    `${BASE}/users/login`,
    JSON.stringify({ email, password }),
    { headers: { "Content-Type": "application/json" } }
  );
  check(loginRes, {
    "logged in OK": (r) => r.status === 200 && r.json("token"),
  });
  const token = loginRes.json("token");

  let prodRes = http.get(`${BASE}/products`);
  check(prodRes, { "got products": (r) => r.status === 200 });
  const productIds = prodRes.json().data.map((p) => p.id);

  return { token, productIds };
}

export default function (data) {
  const headersAuth = {
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${data.token}`,
    },
  };

  check(http.get(`${BASE}/users/profile`, headersAuth), {
    "profile 200": (r) => r.status === 200,
  }) || errorRate.add(1);

  check(http.get(`${BASE}/users/cart`, headersAuth), {
    "cart 200": (r) => r.status === 200,
  }) || errorRate.add(1);

  if (Math.random() < CHECKOUT_RATE) {
    let co = http.get(`${BASE}/buyer/checkout`, headersAuth);
    check(co, {
      "checkout 200": (r) => r.status === 200,
      "has session_id": (r) => !!r.json("session_id"),
    }) || errorRate.add(1);
  } else {
    let h = http.get(`${BASE}/buyer/health`, headersAuth);
    check(h, {
      "health 200": (r) => r.status === 200,
    }) || errorRate.add(1);
  }

  sleep(1);
}
