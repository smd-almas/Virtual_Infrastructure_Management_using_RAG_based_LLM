import json
import matplotlib.pyplot as plt
from datetime import datetime

def load_cpu(file):
    with open(file) as f:
        data = json.load(f)

    values = data["data"]["result"][0]["values"]
    times = [datetime.fromtimestamp(float(t[0])) for t in values]
    cpus = [float(t[1]) for t in values]
    return times, cpus

# Load both datasets
baseline_times, baseline_cpu = load_cpu("baseline_cpu.json")
optimized_times, optimized_cpu = load_cpu("optimized_cpu.json")

# --- Plot ---
plt.figure(figsize=(10,6))
plt.plot(baseline_times, baseline_cpu, label="Baseline", color="red")
plt.plot(optimized_times, optimized_cpu, label="Optimized", color="green")

plt.xlabel("Time")
plt.ylabel("CPU Usage (cores)")
plt.title("Baseline vs Optimized CPU Usage")
plt.legend()

# --- Compute and annotate averages ---
baseline_avg = sum(baseline_cpu) / len(baseline_cpu)
optimized_avg = sum(optimized_cpu) / len(optimized_cpu)

plt.axhline(baseline_avg, color="red", linestyle="--", alpha=0.6)
plt.axhline(optimized_avg, color="green", linestyle="--", alpha=0.6)

plt.text(baseline_times[len(baseline_times)//2], baseline_avg + 0.02,
         f"Baseline avg = {baseline_avg:.4f}", color="red")

plt.text(optimized_times[len(optimized_times)//2], optimized_avg + 0.02,
         f"Optimized avg = {optimized_avg:.4f}", color="green")

# --- Save and show ---
plt.savefig("cpu_comparison.png", dpi=300, bbox_inches="tight")
plt.show()
