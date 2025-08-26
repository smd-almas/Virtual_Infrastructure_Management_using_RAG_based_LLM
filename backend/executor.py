import subprocess
import tempfile
from typing import Union

from k8s_client import (
    scale_deployment,
    create_or_update_yaml,
    apply_autoscaler,
    patch_resource_requests,
    create_loadbalancer_service,
    get_pod_metrics,
    get_services_with_type,
    diagnose_and_fix_issues
)

from prom_query import query_time_series


def execute_command(payload: dict) -> str:
    if "yaml" in payload:
        return apply_yaml(payload["yaml"])
    elif "cli" in payload:
        return run_cli_command(payload["cli"])
    elif "action" in payload:
        return handle_action(payload["action"])
    elif "clarify" in payload:
        return f"Clarification needed: {payload['clarify']}"
    else:
        return "Invalid payload format."


def apply_yaml(yaml_str: str) -> str:
    try:
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".yaml") as tmp:
            tmp.write(yaml_str)
            tmp.flush()
            result = subprocess.run(
                ["kubectl", "apply", "-f", tmp.name],
                capture_output=True,
                text=True,
                check=False
            )
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Error applying YAML: {str(e)}"


def run_cli_command(command: Union[str, list[str]]) -> str:
    if isinstance(command, str):
        command = command.split()
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Error executing command: {str(e)}"


def handle_action(action: Union[str, dict, list]) -> str:
    try:
        if isinstance(action, list):
            results = []
            for step in action:
                result = handle_action(step)
                # Avoid f-string: concatenate safely
                results.append("🔹 Step: {}\n{}".format(step.get("type", "unknown"), result))
            return "\n\n".join(results)

        if isinstance(action, str):
            action = {"type": action}

        action_type = action.get("type")
        name = action.get("name")
        namespace = action.get("namespace", "default")

        if action_type == "optimize_latency":
            if not name:
                return "Missing deployment name for latency optimization."
            patch_result = patch_resource_requests(name=name, namespace=namespace, cpu="100m", memory="128Mi")
            hpa_result = apply_autoscaler(name=name, namespace=namespace, min_replicas=1, max_replicas=5, target_cpu_utilization=60)
            lb_result = create_loadbalancer_service(name=name, namespace=namespace, port=80, target_port=80)
            return (
                "✅ Latency optimization complete for '{}':\n\n"
                "- Resource patch:\n{}\n\n"
                "- HPA setup:\n{}\n\n"
                "- LoadBalancer:\n{}".format(name, patch_result, hpa_result, lb_result)
            )

        elif action_type == "autoscale":
            if not name:
                return "Missing deployment name for autoscaling."
            return apply_autoscaler(
                name=name,
                namespace=namespace,
                min_replicas=action.get("min", 1),
                max_replicas=action.get("max", 5),
                target_cpu_utilization=action.get("cpu", 60)
            )

        elif action_type == "scale":
            if not name:
                return "Missing deployment name for scaling."
            return scale_deployment(
                name=name,
                namespace=namespace,
                replicas=action["replicas"]
            )

        elif action_type == "suggest_scaling":
            if not name:
                return "Missing deployment name for scaling suggestion."
            metrics = get_pod_metrics(name, namespace)
            if not metrics:
                return "No metrics found for deployment '{}'.".format(name)
            cpu_values = [pod["cpu"] for pod in metrics.values() if "cpu" in pod]
            avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else "?"
            return "📈 Suggestion: Deployment '{}' average CPU usage: {} millicores.".format(name, avg_cpu)

        elif action_type == "analyze_metrics":
            if not name:
                return "Missing deployment name for metrics analysis."
            metrics = get_pod_metrics(name, namespace)
            if not metrics:
                return "No metrics found for deployment '{}'.".format(name)
            output = "📊 Resource usage for '{}':\n".format(name)
            for pod, data in metrics.items():
                output += "- {}: CPU={}m | Memory={}Mi\n".format(
                    pod, data.get("cpu", "?"), data.get("memory", "?")
                )
            return output

        elif action_type == "show_exposed_services":
            services = get_services_with_type(types=["LoadBalancer", "NodePort"])
            if not services:
                return "No exposed services found."
            output = "🌐 Exposed Services:\n"
            for svc in services:
                output += "- {} ({}) in {} → Port: {} Target: {}\n".format(
                    svc["name"], svc["type"], svc["namespace"], svc["port"], svc["target_port"]
                )
            return output

        elif action_type == "fix_deployment_issues":
            if not name:
                return "Missing deployment name for fix attempt."
            return diagnose_and_fix_issues(name, namespace)

        elif action_type == "metrics_analysis":
            metric = action.get("metric", "cpu")
            minutes = action.get("minutes", 10)
            step = action.get("step", 15)
            prom_result = query_time_series(metric_name=metric, minutes=minutes, step=step)
            if prom_result["status"] == "success":
                latest_data = prom_result["metrics"][-1] if prom_result["metrics"] else None
                if not latest_data:
                    return "No {} data found in the last {} minutes.".format(metric, minutes)
                return (
                    "📊 {} analysis (last {} min):\n"
                    "Instance: {}\n"
                    "Value: {}%".format(
                        metric.upper(), minutes, latest_data["instance"], latest_data["value"]
                    )
                )
            else:
                return "❌ Error fetching {} metrics: {}".format(metric, prom_result.get("message"))

        elif action_type == "autoscale_based_on_metrics":
            metric = action.get("metric", "cpu")
            if not name:
                return "Missing deployment name."
            data = query_time_series(metric_name=metric, minutes=5, step=15)
            if data["status"] != "success" or not data["metrics"]:
                return "Failed to fetch {} metrics.".format(metric)
            latest = data["metrics"][-1]
            usage = latest["value"]
            try:
                usage_float = float(usage)
                target = min(int(usage_float + 20), 90)
            except:
                target = 60
            result = apply_autoscaler(
                name=name,
                namespace=namespace,
                min_replicas=1,
                max_replicas=5,
                target_cpu_utilization=target
            )
            return (
                "✅ Autoscaling applied based on current {} usage ({}%):\n{}".format(
                    metric, usage, result
                )
            )

        else:
            return "Unknown action type: {}".format(action_type)

    except Exception as e:
        return "Error handling action: {}".format(str(e))
