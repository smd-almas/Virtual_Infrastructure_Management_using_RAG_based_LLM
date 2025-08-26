#!/usr/bin/env python3
import argparse, requests, json, time
from datetime import datetime, timezone

def query_prom(prom_url, query, timeout=30):
    try:
        r = requests.get(f"{prom_url}/api/v1/query", params={"query": query}, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        ts = datetime.now(timezone.utc).isoformat()
        print(f"{ts} ERROR: {e}")
        return None

def collect_metrics(prom_url, namespace, pod_regex, duration, interval, output, timeout, retries):
    start = time.time()
    results = []

    while time.time() - start < duration:
        query = f'sum(rate(container_cpu_usage_seconds_total{{namespace="{namespace}",pod=~"{pod_regex}",container!=""}}[1m])) by (pod)'
        resp = None
        for attempt in range(1, retries+1):
            resp = query_prom(prom_url, query, timeout)
            if resp and 'data' in resp and 'result' in resp['data']:
                break
            else:
                ts = datetime.now(timezone.utc).isoformat()
                print(f"{ts} WARN: empty/failed query (attempt {attempt}/{retries})")
                time.sleep(1)
        if resp and 'data' in resp and 'result' in resp['data']:
            timestamp = datetime.now(timezone.utc).isoformat()
            for r in resp['data']['result']:
                pod = r['metric'].get('pod', 'unknown')
                cpu = float(r['value'][1]) * 1000  # millicores
                results.append({"timestamp": timestamp, "pod": pod, "cpu": cpu})
            print(f"{timestamp} collected {len(resp['data']['result'])} pod metrics")
        else:
            ts = datetime.now(timezone.utc).isoformat()
            print(f"{ts} ERROR: giving up this interval")
        time.sleep(interval)

    with open(output, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Saved {len(results)} samples to {output}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prom-url", required=True)
    parser.add_argument("--namespace", default="default")
    parser.add_argument("--pod-regex", required=True)
    parser.add_argument("--duration", type=int, default=300)
    parser.add_argument("--interval", type=int, default=5)
    parser.add_argument("--output", required=True)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--retries", type=int, default=3)
    args = parser.parse_args()

    collect_metrics(
        args.prom_url, args.namespace, args.pod_regex,
        args.duration, args.interval, args.output, args.timeout, args.retries
    )
