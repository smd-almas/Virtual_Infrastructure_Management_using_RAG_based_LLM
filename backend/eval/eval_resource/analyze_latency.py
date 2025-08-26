import pandas as pd
import matplotlib.pyplot as plt
import os

# Get directory of this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# File paths
baseline_file = os.path.join(SCRIPT_DIR, "baseline_metrics.csv")
optimized_file = os.path.join(SCRIPT_DIR, "optimized_metrics.csv")

# Load datasets
baseline = pd.read_csv(baseline_file)
optimized = pd.read_csv(optimized_file)

# Convert timestamp
baseline["timestamp"] = pd.to_datetime(baseline["timestamp"])
optimized["timestamp"] = pd.to_datetime(optimized["timestamp"])

# Ensure cpu is float
baseline["cpu"] = baseline["cpu"].astype(float)
optimized["cpu"] = optimized["cpu"].astype(float)

# Debug: check time ranges
print("Baseline time range:", baseline["timestamp"].min(), "->", baseline["timestamp"].max())
print("Optimized time range:", optimized["timestamp"].min(), "->", optimized["timestamp"].max())

# --- CPU Comparison Plot ---
plt.figure(figsize=(10, 6))

plt.plot(baseline["timestamp"], baseline["cpu"], label="Baseline", linewidth=2, color="blue")
plt.plot(optimized["timestamp"], optimized["cpu"], label="Optimized", linewidth=2, color="red")

plt.xlabel("Time")
plt.ylabel("CPU Usage (cores)")
plt.title("CPU Usage Comparison")
plt.legend()
plt.grid(True)
plt.tight_layout()

cpu_plot = os.path.join(SCRIPT_DIR, "cpu_comparison.png")
plt.savefig(cpu_plot)
plt.close()
print(f"✅ CPU plot saved to {cpu_plot}")


# --- Summary Table (LaTeX) ---
summary = {
    "Metric": ["CPU Avg (cores)", "CPU Max (cores)"],
    "Baseline": [
        baseline["cpu"].mean(),
        baseline["cpu"].max()
    ],
    "Optimized": [
        optimized["cpu"].mean(),
        optimized["cpu"].max()
    ]
}

df_summary = pd.DataFrame(summary)
latex_table = df_summary.to_latex(index=False, float_format="%.4f")

table_file = os.path.join(SCRIPT_DIR, "resource_comparison_table.tex")
with open(table_file, "w") as f:
    f.write(latex_table)

print(f"✅ CPU plot saved to {cpu_plot}")
print(f"✅ LaTeX table saved to {table_file}")
