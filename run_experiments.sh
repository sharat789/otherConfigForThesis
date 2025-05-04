#!/usr/bin/env bash
set -euo pipefail

# 1) VU counts to test
VUS_LIST=(50 100 200 500)

# 2) Duration of each k6 run
DURATION="1m"

# 3) Your k6 script
K6_SCRIPT="test.js"

# # 4) Gremlin API settings
GREMLIN_TEAM_ID="930f7543-b993-4b6b-8f75-43b9930b6bad"
GREMLIN_TOKEN="Bearer Yy00MTEzYzNiYS1kNjNlLTU3MzMtYmRkYy1kNjU4OWMwMmUyNTM6YWFjNzVlZWE3M2JjYjFkNTNjMjFhMjhlODU3NzgzMGRiMDBmYmMwZDk1ZWJlNDE4NTljZWFmOGEzYTM0OGRmOWY0ZjcwYjJkM2QxNWRhODkzYmNhZWE5Njg2NzkxNzg5MGFkYmNlNmNmZDYxZThmZjFkNjRhZDg2NjhiYmZhN2U6YThiNzNhMjUtNGEwOS00M2Y1LWI3M2EtMjU0YTA5MjNmNWZl"
GREMLIN_URL="https://api.gremlin.com/v1/attacks?teamId=${GREMLIN_TEAM_ID}"

# # 5) Build the JSON payload for the Gremlin attack
# The body changes based on the attack that's ran on Gremlin
GREMLIN_PAYLOAD=$(cat <<'EOF'
{
  "attackConfiguration": {
    "command": {
      "infraCommandType": "shutdown",
      "infraCommandArgs": {
        "type": "shutdown",
        "delay": 1,
        "reboot": true,
        "cliArgs": [
          "shutdown",
          "-d",
          "1",
          "-r"
        ]
      }
    },
    "targets": [
      {
        "targetingStrategy": {
          "type": "Kubernetes",
          "isAll": false,
          "containerSelection": {
            "selectionType": "ANY",
            "containerNames": []
          },
          "names": [
            {
              "clusterId": "minikube",
              "kind": "DEPLOYMENT",
              "namespace": "ingress-nginx",
              "name": "ingress-nginx-controller"
            }
          ]
        }
      }
    ],
    "sampling": {
      "type": "Exact",
      "count": 1
    }
  },
  "includeNewTargets": true
}
EOF
)

echo "Starting experiments..."

for VUS in "${VUS_LIST[@]}"; do
  echo
  echo "=== Running with $VUS VUs ==="

  # 1) Kick off Gremlin attack in the background
  curl -s -X POST "$GREMLIN_URL" \
    -H "Content-Type: application/json;charset=utf-8" \
    -H "Authorization: $GREMLIN_TOKEN" \
    -d "$GREMLIN_PAYLOAD" & GREMLIN_PID=$!

  sleep 5

  # 3) Run k6, outputting raw JSON for later parsing
  OUT_JSON="k6-${VUS}.json"
  k6 run \
    --vus "$VUS" \
    --duration "$DURATION" \
    --out json="$OUT_JSON" \
    "$K6_SCRIPT" || true

  # 4) Wait for Gremlin to finish (ignore its exit code)
  wait $GREMLIN_PID || true

  # 5) Roll out your deployments again
  # This check is done to see if the deployment which is targeted 
  # is back up before running experiment again for the next user load
  echo "Waiting for deployments to roll out..."
  for DEP in ingress-nginx-controller; do
    kubectl rollout status deployment/"$DEP" -n ingress-nginx --timeout=2m
  done

  # 6) Let readiness probes settle
  echo "Sleeping 10s to let probes settle..."
  sleep 10

  echo "→ Completed VUs=$VUS, JSON saved to $OUT_JSON"
done

echo
echo "All experiments finished. Raw JSON files are in the current directory."