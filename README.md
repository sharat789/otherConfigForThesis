## 📁 Project Files Overview

### `extractTabulate.py`
This Python script is responsible for **parsing and extracting key performance metrics** (e.g., latency, success rate, throughput) from K6 test output files. It generates **tabular summaries** to help compare scenarios and support result analysis for the thesis.

---

### `test.js`
A **K6 load test script** that defines:
- The target API endpoints (e.g., `/users/profile`, `/buyer/checkout`)
- Expected behaviors and success checks
- The request flow used to simulate user behavior during performance and chaos experiments

---

### `run_experiments.sh`
A Bash script that:
- Iterates through a list of **Virtual User (VU)** load values
- Triggers a **Gremlin chaos attack** (e.g., pod shutdown) for each run
- Executes the `test.js` script with defined VUs and duration
- Waits for system recovery and collects output in structured JSON files

This script automates the **chaos testing workflow**.

---

### `monitoringConfig.json`
Grafana dashboard configuration used to:
- Visualize key metrics such as **latency**, **error rates**, and **request rate by route**
- Monitor system behavior in real time during chaos and load experiments
- Capture status code distribution, spikes, and anomalies in services

---
