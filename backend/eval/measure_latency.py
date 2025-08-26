import time
import requests
import pandas as pd
import matplotlib.pyplot as plt
import os

# Config
API_URL = "http://localhost:8000/ask"  # adjust if backend is on a different port
OUTPUT_DIR = "eval"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Sample queries for latency testing
QUERIES = [
    "Deploy an nginx pod",
    "Get all pods in the default namespace",
    "Scale deployment myapp to 3 replicas",
    "Show me the CPU usage of all pods",
    "Fix the failing deployment myapp",
    "Expose myapp via a LoadBalancer",
]

def measure_latency():
    results = []

    for q in QUERIES:
        print(f"Testing: {q}")
        start = time.time()
        try:
            resp = requests.post(API_URL, json={"query": q}, timeout=60)
            latency = time.time() - start
            status = "success" if resp.status_code == 200 else f"HTTP {resp.status_code}"
        except Exception as e:
            latency = None
            status = f"error: {e}"

        results.append({
            "query": q,
            "latency_sec": latency,
            "status": status,
        })

    df = pd.DataFrame(results)
    csv_path = os.path.join(OUTPUT_DIR, "latency_results.csv")
    df.to_csv(csv_path, index=False)
    print(f"[✔] Saved latency results to {csv_path}")

    # Plot bar chart of latencies
    success_df = df[df["latency_sec"].notnull()]
    plt.figure(figsize=(10, 5))
    plt.barh(success_df["query"], success_df["latency_sec"])
    plt.xlabel("Latency (seconds)")
    plt.title("Latency per Query")
    plt.tight_layout()
    plot_path = os.path.join(OUTPUT_DIR, "latency_results.png")
    plt.savefig(plot_path)
    print(f"[✔] Saved plot to {plot_path}")

    return df

if __name__ == "__main__":
    df = measure_latency()
    print("\nLatency Results:\n", df)
