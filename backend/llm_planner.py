import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=api_key)


def extract_json(text: str):
    """
    Extract JSON object or array from a string.
    """
    match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
    if match:
        return match.group(1)
    return None


def classify_intent(query: str) -> str:
    """
    Classify the user input as 'question' or 'command'.
    """
    prompt = f"""
Classify the following input as either "question" or "command".

User Input:
\"{query}\"

Respond ONLY with: question or command.
"""
    response = openai_client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content.strip().lower()


def plan_action(query: str):
    """
    Convert user query into structured Kubernetes action plan.
    """
    planning_prompt = f"""
You are a Kubernetes assistant. Convert natural language commands into JSON action plans.

💡 Output formats:
- Single action:
  {{ "type": "yaml", "content": "<YAML>" }}
  {{ "type": "cli", "content": "kubectl ..." }}
  {{ "type": "scale", "name": "<deployment>", "replicas": 3 }}
  {{ "type": "autoscale", "name": "<deployment>", "min_replicas": 2, "max_replicas": 5, "target_cpu": 60 }}
  {{ "type": "optimize_latency", "name": "<deployment>" }}
  {{ "type": "suggest_scaling", "name": "<deployment>" }}
  {{ "type": "analyze_metrics", "name": "<deployment>", "namespace": "<namespace>" }}
  {{ "type": "show_exposed_services" }}
  {{ "type": "fix_deployment_issues", "name": "<deployment>", "namespace": "<namespace>" }}
  {{ "type": "autoscale_based_on_metrics", "name": "<deployment>", "metric": "cpu" }}
  {{ "type": "metrics_analysis", "metric": "cpu", "minutes": 10, "step": 15 }}

- Multi-step: JSON array of actions

⚠ Rules:
- Use `yaml` only for creating deployments.
- Use `cli` for direct kubectl commands.
- Default namespace to "default" if not provided.
- Respond ONLY with valid JSON. No explanation, no comments, no extra text.

📝 Examples:

User: "Deploy nginx with 2 replicas"
→ {{ "type": "yaml", "content": "apiVersion: apps/v1\\nkind: Deployment\\nmetadata:\\n  name: nginx\\nspec:\\n  replicas: 2\\n  selector:\\n    matchLabels:\\n      app: nginx\\n  template:\\n    metadata:\\n      labels:\\n        app: nginx\\n    spec:\\n      containers:\\n      - name: nginx\\n        image: nginx" }}

User: "Create a deployment named myapp with image myimage:latest and 3 replicas"
→ {{ "type": "yaml", "content": "apiVersion: apps/v1\\nkind: Deployment\\nmetadata:\\n  name: myapp\\nspec:\\n  replicas: 3\\n  selector:\\n    matchLabels:\\n      app: myapp\\n  template:\\n    metadata:\\n      labels:\\n        app: myapp\\n    spec:\\n      containers:\\n      - name: myapp\\n        image: myimage:latest" }}

User: "Scale myapp to 5 replicas"
→ {{ "type": "scale", "name": "myapp", "replicas": 5 }}

User: "Enable autoscaling for myapp from 2 to 6 replicas at 70% CPU"
→ {{ "type": "autoscale", "name": "myapp", "min_replicas": 2, "max_replicas": 6, "target_cpu": 70 }}

User: "Optimize latency for webapp"
→ {{ "type": "optimize_latency", "name": "webapp" }}

User: "Show exposed services"
→ {{ "type": "show_exposed_services" }}

User: "Run kubectl get pods"
→ {{ "type": "cli", "content": "kubectl get pods" }}

User: "Analyze metrics for myapp in prod namespace"
→ {{ "type": "analyze_metrics", "name": "myapp", "namespace": "prod" }}

User: "Fix issues in payment-service in staging"
→ {{ "type": "fix_deployment_issues", "name": "payment-service", "namespace": "staging" }}

User: "Suggest scaling for backend"
→ {{ "type": "suggest_scaling", "name": "backend" }}

User: "Autoscale based on current cpu usage for backend"
→ {{ "type": "autoscale_based_on_metrics", "name": "backend", "metric": "cpu" }}

User: "Analyze CPU usage over time"
→ {{ "type": "metrics_analysis", "metric": "cpu", "minutes": 10, "step": 15 }}

User: "Diagnose and fix webapp in default namespace"
→ {{ "type": "fix_deployment_issues", "name": "webapp", "namespace": "default" }}

User Input:
\"{query}\"
"""

    response = openai_client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": planning_prompt}],
        temperature=0.2
    )
    result = response.choices[0].message.content.strip()

    json_str = extract_json(result)
    if not json_str:
        return {
            "type": "clarify",
            "hint": "Failed to parse action plan. Please rephrase or simplify the command."
        }

    try:
        parsed = json.loads(json_str)

        def ensure_namespace(obj):
            if isinstance(obj, dict):
                if obj.get("type") in ["analyze_metrics", "fix_deployment_issues"]:
                    obj.setdefault("namespace", "default")
            return obj

        if isinstance(parsed, list):
            return [ensure_namespace(p) for p in parsed]
        else:
            return ensure_namespace(parsed)

    except json.JSONDecodeError:
        return {
            "type": "clarify",
            "hint": "Invalid JSON in plan. Please rephrase your command."
        }


def extract_context(query: str) -> dict:
    """
    Extract deployment-related values from query.
    """
    prompt = f"""
Extract these fields from the input if present:
- name
- namespace
- image
- cpu
- memory
- replicas
- port
- target_port

Respond ONLY with JSON.

User Input:
\"{query}\"
"""
    response = openai_client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    result = response.choices[0].message.content.strip()
    json_str = extract_json(result)
    if not json_str:
        return {}
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return {}
