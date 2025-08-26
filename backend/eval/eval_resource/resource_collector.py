import csv
import time
import requests
from datetime import datetime

PROM_URL = "http://localhost:19092/api/v1/query"
NAMESPACE = "default"
DEPLOYMENT = "test-app"
OUTPUT = "baseline_metrics.csv"

def query_prometheus(query):
    r = requests.get(PROM_URL, params={'query': query})
    result = r.json()['data']['result']
    if result:
        return float(result[0]['value'][1])
    return None

def collect_metrics(duration=60, interval=5):
    with open(OUTPUT, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "cpu", "memory"])
        start = time.time()
        while time.time() - start < duration:
            ts = datetime.now().strftime("%H:%M:%S")

            cpu = query_prometheus(f'rate(container_cpu_usage_seconds_total{{namespace="{NAMESPACE}",pod=~"{DEPLOYMENT}.*"}}[1m])')
            mem = query_prometheus(f'container_memory_usage_bytes{{namespace="{NAMESPACE}",pod=~"{DEPLOYMENT}.*"}}')

            writer.writerow([ts, cpu if cpu else 0, mem if mem else 0])
            f.flush()
            time.sleep(interval)

if __name__ == "__main__":
    collect_metrics(duration=60, interval=5)
