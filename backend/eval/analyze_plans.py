#!/usr/bin/env python3
"""
analyze_plans.py

Reads test_prompts.txt, calls llm_planner.plan_action() for each prompt,
compares the result with expected_plans.json, writes logs and summary.

Outputs:
 - eval/raw_plans.json              (actual LLM outputs)
 - eval/comparison.csv              (timestamp,prompt,expected,actual,pass,notes)
 - eval/summary.json                (counts,accuracy,per-category stats)
 - eval/accuracy_per_category.png   (bar chart)
 - eval/overall_pie.png             (pie chart)
 - eval/accuracy_table.tex          (LaTeX table for per-category accuracy)
 - eval/overall_accuracy.tex        (LaTeX macro with overall accuracy number)
"""

import os
import sys
import json
import csv
from datetime import datetime
from pprint import pprint

import matplotlib.pyplot as plt
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTDIR = "eval"
os.makedirs(OUTDIR, exist_ok=True)

try:
    from llm_planner import plan_action
except Exception as e:
    print("ERROR: could not import plan_action from llm_planner.py:", e)
    print("Make sure analyze_plans.py is run from your project root where llm_planner.py lives.")
    sys.exit(1)

TEST_PROMPTS_FILE = "test_prompts.txt"
EXPECTED_FILE = "expected_plans.json"
RAW_OUT = os.path.join(OUTDIR, "raw_plans.json")
CSV_OUT = os.path.join(OUTDIR, "comparison.csv")
SUMMARY_OUT = os.path.join(OUTDIR, "summary.json")


def load_prompts(path):
    lines = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f.readlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            lines.append(line)
    return lines


def load_expected(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_plan(obj):
    if isinstance(obj, (dict, list)):
        try:
            return ("json", json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
        except Exception:
            return ("str", str(obj).strip())
    elif isinstance(obj, str):
        return ("str", obj.strip())
    else:
        return ("str", str(obj).strip())


def compare_plans(expected, actual):
    e_type, e_norm = normalize_plan(expected)
    a_type, a_norm = normalize_plan(actual)

    if e_type == a_type and e_norm == a_norm:
        return True, "exact match"

    try:
        if e_type == "json" and a_type == "json":
            e_obj = json.loads(e_norm)
            a_obj = json.loads(a_norm)
            if isinstance(e_obj, dict) and isinstance(a_obj, dict):
                if e_obj.get("type") == a_obj.get("type"):
                    if e_obj.get("type") == "yaml":
                        e_content = e_obj.get("content", "").strip()
                        a_content = a_obj.get("content", "").strip()
                        if e_content and a_content and e_content.splitlines()[0] == a_content.splitlines()[0]:
                            return True, "yaml-first-line-match (approx)"
                    return True, "same-type (partial match)"
    except Exception:
        pass

    return False, "mismatch"


def category_of_expected(exp):
    if isinstance(exp, dict):
        t = exp.get("type")
        return t or "unknown"
    if isinstance(exp, list):
        return "multi-step"
    if isinstance(exp, str):
        return "yaml_or_text"
    return "unknown"


def main():
    if not os.path.exists(TEST_PROMPTS_FILE):
        print(f"Missing {TEST_PROMPTS_FILE}. Put your prompts there (one per non-comment line).")
        sys.exit(1)
    if not os.path.exists(EXPECTED_FILE):
        print(f"Missing {EXPECTED_FILE}. Create ground truth expected plans for each prompt.")
        sys.exit(1)

    prompts = load_prompts(TEST_PROMPTS_FILE)
    expected = load_expected(EXPECTED_FILE)

    results = {}
    rows = []
    summary = {"total": 0, "passed": 0, "failed": 0, "by_category": {}}

    timestamp = datetime.utcnow().isoformat() + "Z"

    for prompt in prompts:
        print("\n---")
        print("Prompt:", prompt)
        summary["total"] += 1

        try:
            plan = plan_action(prompt)
        except Exception as e:
            plan = {"type": "error", "error": str(e)}

        results[prompt] = plan
        exp = expected.get(prompt)

        if exp is None:
            note = "no expected plan provided"
            passed = False
            summary["failed"] += 1
            cat = "no-expected"
        else:
            passed, note = compare_plans(exp, plan)
            if passed:
                summary["passed"] += 1
            else:
                summary["failed"] += 1
            cat = category_of_expected(exp)

        summary["by_category"].setdefault(cat, {"total": 0, "passed": 0, "failed": 0})
        summary["by_category"][cat]["total"] += 1
        if passed:
            summary["by_category"][cat]["passed"] += 1
        else:
            summary["by_category"][cat]["failed"] += 1

        rows.append({
            "timestamp": timestamp,
            "prompt": prompt,
            "expected": json.dumps(exp, ensure_ascii=False) if exp is not None else "",
            "actual": json.dumps(plan, ensure_ascii=False),
            "pass": passed,
            "note": note
        })

        print("Actual plan:", json.dumps(plan, indent=2, ensure_ascii=False))
        print("Expected plan:", json.dumps(exp, indent=2, ensure_ascii=False))
        print("Result:", "PASS" if passed else "FAIL", "-", note)

    with open(RAW_OUT, "w", encoding="utf-8") as f:
        json.dump({"timestamp": timestamp, "results": results}, f, indent=2, ensure_ascii=False)

    with open(CSV_OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "prompt", "expected", "actual", "pass", "note"])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    accuracy = summary["passed"] / summary["total"] if summary["total"] else 0.0
    summary_obj = {
        "timestamp": timestamp,
        "total_cases": summary["total"],
        "passed": summary["passed"],
        "failed": summary["failed"],
        "accuracy": round(accuracy, 4),
        "by_category": summary["by_category"],
    }

    with open(SUMMARY_OUT, "w", encoding="utf-8") as f:
        json.dump(summary_obj, f, indent=2, ensure_ascii=False)

    print("\n\n=== SUMMARY ===")
    pprint(summary_obj)
    print(f"\nRaw outputs -> {RAW_OUT}")
    print(f"CSV comparison -> {CSV_OUT}")
    print(f"Summary -> {SUMMARY_OUT}")

    # === Plotting ===
    categories = list(summary_obj["by_category"].keys())
    accuracies = []
    for cat, stats in summary_obj["by_category"].items():
        acc = stats["passed"] / stats["total"] if stats["total"] else 0
        accuracies.append(acc)

    # Bar chart
    plt.figure(figsize=(8, 5))
    plt.bar(categories, accuracies, color="skyblue")
    plt.ylim(0, 1)
    plt.ylabel("Accuracy")
    plt.title("Accuracy per Category")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTDIR, "accuracy_per_category.png"))
    plt.close()

    # Pie chart
    sizes = [summary_obj["passed"], summary_obj["failed"]]
    labels = ["Correct", "Incorrect"]
    colors = ["#4CAF50", "#F44336"]

    plt.figure(figsize=(5, 5))
    plt.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%", startangle=140)
    plt.title("Overall Plan Accuracy")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTDIR, "overall_pie.png"))
    plt.close()

    # === LaTeX exports ===
    df = pd.DataFrame([
        {"Category": cat,
         "Total": stats["total"],
         "Passed": stats["passed"],
         "Failed": stats["failed"],
         "Accuracy (%)": round((stats["passed"] / stats["total"]) * 100, 1) if stats["total"] else 0}
        for cat, stats in summary_obj["by_category"].items()
    ])

    latex_table = df.to_latex(index=False, caption="Accuracy per Category", label="tab:accuracy")
    with open(os.path.join(OUTDIR, "accuracy_table.tex"), "w") as f:
        f.write(latex_table)

    # Overall accuracy macro
    overall_tex = f"\\newcommand{{\\OverallAccuracy}}{{{round(accuracy*100,1)}\\%}}"
    with open(os.path.join(OUTDIR, "overall_accuracy.tex"), "w") as f:
        f.write(overall_tex)

    print(f"Charts saved -> {OUTDIR}/accuracy_per_category.png , {OUTDIR}/overall_pie.png")
    print(f"LaTeX outputs -> {OUTDIR}/accuracy_table.tex , {OUTDIR}/overall_accuracy.tex")
    print("\nDone.")


if __name__ == "__main__":
    main()
