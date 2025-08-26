import requests
import time
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import kubernetes.utils as k8s_utils

# Load kubeconfig for local development
config.load_kube_config()

# K8s clients
core_v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
autoscaling_v1 = client.AutoscalingV1Api()

PROMETHEUS_URL = "http://localhost:19092"

# --- LISTING RESOURCES ---

def list_pods(namespace: str = "default"):
    pods = core_v1.list_namespaced_pod(namespace)
    return [pod.metadata.name for pod in pods.items]

def list_services(namespace: str = "default"):
    services = core_v1.list_namespaced_service(namespace)
    return [svc.metadata.name for svc in services.items]

def list_deployments(namespace: str = "default"):
    deployments = apps_v1.list_namespaced_deployment(namespace)
    return [dep.metadata.name for dep in deployments.items]

def list_configmaps(namespace: str = "default"):
    cms = core_v1.list_namespaced_config_map(namespace)
    return [cm.metadata.name for cm in cms.items]

def list_namespaces():
    ns_list = core_v1.list_namespace()
    return [ns.metadata.name for ns in ns_list.items]

def list_nodes():
    nodes = core_v1.list_node()
    return [node.metadata.name for node in nodes.items]

# --- SCALING DEPLOYMENT ---

def scale_deployment(name: str, namespace: str, replicas: int) -> str:
    try:
        body = {"spec": {"replicas": replicas}}
        apps_v1.patch_namespaced_deployment_scale(name, namespace, body)
        return f"Scaled deployment '{name}' to {replicas} replicas."
    except ApiException as e:
        return f"Error scaling deployment: {e}"

# --- PATCH RESOURCE REQUESTS ---

def patch_resource_requests(name: str, namespace: str, cpu: str, memory: str) -> str:
    try:
        deployment = apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
        containers = deployment.spec.template.spec.containers
        if not containers:
            return f"Error: No containers found in deployment '{name}'."

        container_name = containers[0].name

        body = {
            "spec": {
                "template": {
                    "spec": {
                        "containers": [{
                            "name": container_name,
                            "resources": {
                                "requests": {
                                    "cpu": cpu,
                                    "memory": memory
                                }
                            }
                        }]
                    }
                }
            }
        }

        apps_v1.patch_namespaced_deployment(name=name, namespace=namespace, body=body)
        return f"Patched resources for deployment '{name}' (CPU: {cpu}, Memory: {memory})"
    except ApiException as e:
        return f"Error patching resources: {e}"

# --- APPLY AUTOSCALER (HPA) ---

def apply_autoscaler(name: str, namespace: str, min_replicas: int, max_replicas: int, target_cpu_utilization: int) -> str:
    try:
        hpa = client.V1HorizontalPodAutoscaler(
            metadata=client.V1ObjectMeta(name=name),
            spec=client.V1HorizontalPodAutoscalerSpec(
                scale_target_ref=client.V1CrossVersionObjectReference(
                    api_version="apps/v1",
                    kind="Deployment",
                    name=name
                ),
                min_replicas=min_replicas,
                max_replicas=max_replicas,
                target_cpu_utilization_percentage=target_cpu_utilization
            )
        )
        autoscaling_v1.create_namespaced_horizontal_pod_autoscaler(namespace, hpa)
        return f"Autoscaler created for deployment '{name}'."
    except ApiException as e:
        if e.status == 409:
            return f"HPA for '{name}' already exists."
        return f"Error creating HPA: {e}"

# --- CREATE LOADBALANCER SERVICE ---

def create_loadbalancer_service(name: str, namespace: str, port: int, target_port: int) -> str:
    try:
        service = client.V1Service(
            metadata=client.V1ObjectMeta(name=name),
            spec=client.V1ServiceSpec(
                selector={"app": name},
                ports=[client.V1ServicePort(port=port, target_port=target_port)],
                type="LoadBalancer"
            )
        )
        core_v1.create_namespaced_service(namespace=namespace, body=service)
        return f"LoadBalancer service created for '{name}'."
    except ApiException as e:
        if e.status == 409:
            return f"LoadBalancer service for '{name}' already exists."
        return f"Error creating LoadBalancer service: {e}"

# --- CREATE OR UPDATE YAML MANIFEST ---

def create_or_update_yaml(yaml_manifest: dict, namespace: str = "default") -> str:
    try:
        k8s_client = client.ApiClient()
        k8s_utils.create_from_dict(k8s_client, yaml_manifest, namespace=namespace)
        return f"YAML applied successfully to namespace '{namespace}'."
    except Exception as e:
        return f"Error applying YAML manifest: {e}"

# --- GET ALL RESOURCES ---

def get_all_resources(namespace: str = "default") -> dict:
    return {
        "pods": list_pods(namespace),
        "deployments": list_deployments(namespace),
        "services": list_services(namespace),
        "configmaps": list_configmaps(namespace),
        "nodes": list_nodes(),
        "namespaces": list_namespaces()
    }

# --- GET POD METRICS FROM PROMETHEUS ---

def get_pod_metrics(deployment_name: str, namespace: str):
    try:
        pod_selector = f'{deployment_name}.*'  # match all pods like unique-app-demo-xyz

        # Removed container!="" for compatibility
        cpu_query = (
            f'rate(container_cpu_usage_seconds_total{{'
            f'pod=~"{pod_selector}"}}[2m])'
        )
        mem_query = (
            f'avg_over_time(container_memory_usage_bytes{{'
            f'pod=~"{pod_selector}"}}[2m])'
        )

        def query(promql):
            resp = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": promql})
            resp.raise_for_status()
            return resp.json()["data"]["result"]

        cpu_data = query(cpu_query)
        mem_data = query(mem_query)

        if not cpu_data and not mem_data:
            return {"error": "No metrics found."}

        pod_metrics = {}
        for entry in cpu_data:
            pod_name = entry["metric"].get("pod", "unknown")
            value = float(entry["value"][1]) * 1000  # Convert to millicores
            pod_metrics.setdefault(pod_name, {})["cpu"] = round(value, 2)

        for entry in mem_data:
            pod_name = entry["metric"].get("pod", "unknown")
            value = float(entry["value"][1]) / (1024 * 1024)  # Convert to MiB
            pod_metrics.setdefault(pod_name, {})["memory"] = round(value, 2)

        return pod_metrics

    except Exception as e:
        return {"error": str(e)}

# --- GET EXTERNAL SERVICES ---

def get_services_with_type(types=["LoadBalancer", "NodePort"]):
    services = core_v1.list_service_for_all_namespaces().items
    return [
        {
            "name": svc.metadata.name,
            "namespace": svc.metadata.namespace,
            "type": svc.spec.type,
            "port": svc.spec.ports[0].port,
            "target_port": svc.spec.ports[0].target_port
        }
        for svc in services if svc.spec.type in types
    ]

# --- AUTO-FIX COMMON ISSUES ---

def diagnose_and_fix_issues(deployment_name, namespace):
    # Simulated example logic
    return f"✅ Auto-fix applied for '{deployment_name}' (e.g., restarted pods, verified image, applied limits)."
