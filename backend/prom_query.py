import requests
import time

PROMETHEUS_URL = "http://localhost:19092"

QUERIES = {
    "cpu": '100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[2m])) * 100)',
    "memory": '100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))',
    "disk": '100 - ((node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100)',
    "net_rx": 'rate(node_network_receive_bytes_total[2m])',
    "net_tx": 'rate(node_network_transmit_bytes_total[2m])',
}

def query_time_series(metric_name: str, minutes: int = 10, step: int = 10):
    """
    Query historical time-series data for a given metric.
    Default: last 10 minutes with 10-second step.
    """
    promql = QUERIES.get(metric_name)
    if not promql:
        return {"status": "error", "message": f"Unsupported metric: {metric_name}"}

    end = int(time.time())
    start = end - (minutes * 60)

    try:
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query_range",
            params={
                "query": promql,
                "start": start,
                "end": end,
                "step": step,
            },
        )
        response.raise_for_status()
        results = response.json().get("data", {}).get("result", [])

        series = []
        for item in results:
            metric = item.get("metric", {})
            values = item.get("values", [])

            # Improve instance labeling
            label = (
                metric.get("instance") or
                metric.get("exported_instance") or
                metric.get("device") or
                metric.get("interface") or
                metric.get("job") or
                "unknown"
            )

            for ts, val in values:
                try:
                    value = float(val)
                    series.append({
                        "timestamp": int(float(ts)),
                        "instance": label,
                        "value": round(value, 2),
                    })
                except ValueError:
                    continue

        return {"status": "success", "metrics": series}

    except requests.RequestException as e:
        return {"status": "error", "message": f"Prometheus error: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Unexpected error: {str(e)}"}
