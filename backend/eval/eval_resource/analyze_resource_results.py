#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import argparse
from datetime import datetime

def load_csv(path):
    df = pd.read_csv(path)
    # coerce numeric
    df['cpu_mcores'] = pd.to_numeric(df['cpu_mcores'], errors='coerce')
    df['mem_mib'] = pd.to_numeric(df['mem_mib'], errors='coerce')
    return df

def summarize(df):
    # per-pod averages
    group = df.groupby('pod').agg({'cpu_mcores':'mean','mem_mib':'mean','timestamp':'count'}).rename(columns={'timestamp':'samples'})
    overall = {
        'avg_cpu_mcores': df['cpu_mcores'].mean(skipna=True),
        'avg_mem_mib': df['mem_mib'].mean(skipna=True),
        'samples': len(df)
    }
    return group, overall

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--before", default="baseline_metrics.csv")
    p.add_argument("--after", default="optimized_metrics.csv")
    p.add_argument("--out-prefix", default="eval_resource")
    args = p.parse_args()

    before = load_csv(args.before)
    after = load_csv(args.after)

    b_group, b_overall = summarize(before)
    a_group, a_overall = summarize(after)

    print("=== BEFORE overall ===")
    print(b_overall)
    print("\n=== AFTER overall ===")
    print(a_overall)

    # Percent change
    def pct_change(old, new):
        try:
            return (new-old)/old*100.0
        except:
            return None

    cpu_change = pct_change(b_overall['avg_cpu_mcores'], a_overall['avg_cpu_mcores'])
    mem_change = pct_change(b_overall['avg_mem_mib'], a_overall['avg_mem_mib'])

    print("\nPercent change (after vs before):")
    print(f"CPU (mcores): {cpu_change:.2f}%")
    print(f"Memory (MiB): {mem_change:.2f}%")

    # Save per-pod tables
    b_group.to_csv(f"{args.out_prefix}_before_per_pod.csv")
    a_group.to_csv(f"{args.out_prefix}_after_per_pod.csv")

    # Plots
    plt.figure(figsize=(6,4))
    plt.bar(['before','after'], [b_overall['avg_cpu_mcores'], a_overall['avg_cpu_mcores']])
    plt.ylabel("Avg CPU (mcores)")
    plt.title("Avg CPU before vs after")
    plt.tight_layout()
    plt.savefig(f"{args.out_prefix}_cpu_before_after.png")
    plt.close()

    plt.figure(figsize=(6,4))
    plt.bar(['before','after'], [b_overall['avg_mem_mib'], a_overall['avg_mem_mib']])
    plt.ylabel("Avg Memory (MiB)")
    plt.title("Avg Memory before vs after")
    plt.tight_layout()
    plt.savefig(f"{args.out_prefix}_mem_before_after.png")
    plt.close()

    # Write summary JSON
    import json
    summary = {
        "before": b_overall,
        "after": a_overall,
        "cpu_pct_change": cpu_change,
        "mem_pct_change": mem_change
    }
    with open(f"{args.out_prefix}_summary.json","w") as f:
        json.dump(summary, f, indent=2)

    print("\nSaved results and plots with prefix", args.out_prefix)
