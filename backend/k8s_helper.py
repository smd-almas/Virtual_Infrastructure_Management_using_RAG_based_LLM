from kubernetes import client, config
import os

def load_k8s_config():
    if os.getenv("KUBERNETES_SERVICE_HOST"):
        config.load_incluster_config()
    else:
        config.load_kube_config()

load_k8s_config()

def get_pod_statuses(namespace="default"):
    v1 = client.CoreV1Api()
    pods = v1.list_namespaced_pod(namespace)
    statuses = []
    for pod in pods.items:
        statuses.append({
            "name": pod.metadata.name,
            "status": pod.status.phase,
            "node": pod.spec.node_name
        })
    return statuses

def get_deployments(namespace="default"):
    apps_v1 = client.AppsV1Api()
    deployments = apps_v1.list_namespaced_deployment(namespace)
    return [dep.metadata.name for dep in deployments]

def scale_deployment(name, replicas, namespace="default"):
    apps_v1 = client.AppsV1Api()
    body = {"spec": {"replicas": replicas}}
    apps_v1.patch_namespaced_deployment_scale(name, namespace, body)
    return f"Scaled deployment {name} to {replicas} replicas"
