import os
import json
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from openai import OpenAI, APIConnectionError, OpenAIError

from llm_planner import classify_intent, plan_action, extract_context
from embeddings import search_docs, generate_answer
from executor import apply_yaml, handle_action, execute_command
from k8s_client import (
    get_all_resources,
    get_pod_metrics,
    get_services_with_type,
    diagnose_and_fix_issues,
)
from database import Conversation

# Load .env variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Chat handler entrypoint
def process_query(query: str, db: Session):
    try:
        # Step 1: Determine user intent
        intent = classify_intent(query)

        if intent == "question":
            # Step 2: RAG flow
            docs = search_docs(query)
            context = "\n---\n".join(docs["documents"][0]) if docs["documents"] else ""
            answer = generate_answer(query, context)

            store_message(query, answer, db)
            return {"type": "answer", "result": answer}

        elif intent == "command":
            # Step 3: LLM plans the command
            plan = plan_action(query)

            if isinstance(plan, str):
                result = execute_command(plan)
                store_message(query, result, db)
                return {"type": "command", "result": result}

            elif isinstance(plan, list):
                combined_results = []
                for step in plan:
                    result = handle_step(step)
                    combined_results.append(result)

                final_output = "\n\n".join(combined_results)
                store_message(query, final_output, db)
                return {"type": "multi-step", "result": final_output}

            elif isinstance(plan, dict):
                print("DEBUG: LLM Plan =", plan)
                plan_type = plan.get("type")

                if plan_type == "yaml":
                    result = execute_command({"yaml": plan["content"]})

                elif plan_type == "cli":
                    result = execute_command({"cli": plan["content"]})

                elif plan_type == "clarify":
                    return {
                        "type": "clarify",
                        "missing": plan.get("missing"),
                        "hint": plan.get("hint")
                    }

                else:
                    result = handle_step(plan)

                store_message(query, result, db)
                return {"type": "action", "result": result}

        return {"type": "error", "message": "Unknown intent type."}

    except APIConnectionError as e:
        return {"type": "error", "message": f"Connection error: {str(e)}"}

    except OpenAIError as e:
        return {"type": "error", "message": f"LLM error: {str(e)}"}

    except Exception as e:
        return {"type": "error", "message": f"Unhandled error: {str(e)}"}


# Handle structured action
def handle_step(step: dict) -> str:
    action_type = step.get("type")

    if action_type == "yaml":
        return execute_command({"yaml": step["content"]})

    elif action_type == "cli":
        return execute_command({"cli": step["content"]})

    elif action_type == "analyze_metrics":
        name = step.get("name")
        namespace = step.get("namespace", "default")
        metrics = get_pod_metrics(name, namespace)
        return f"📊 Metrics for {name}:\n" + json.dumps(metrics, indent=2)

    elif action_type == "show_exposed_services":
        services = get_services_with_type()
        return f"🌐 Exposed Services:\n" + json.dumps(services, indent=2)

    elif action_type == "fix_deployment_issues":
        name = step.get("name")
        namespace = step.get("namespace", "default")
        return diagnose_and_fix_issues(name, namespace)

    else:
        return handle_action(step)


# Optional: Extract image, name, replicas, etc. from query
def extract_deployment_context(prompt: str):
    return extract_context(prompt)

# Fetch chat history from database
def get_history(db: Session):
    records = db.query(Conversation).order_by(Conversation.timestamp.desc()).all()
    return [
        {"query": r.user_query, "response": r.bot_response, "timestamp": str(r.timestamp)}
        for r in records
    ]

# Save chat interaction to DB
def store_message(query: str, response: str, db: Session):
    record = Conversation(user_query=query, bot_response=response)
    db.add(record)
    db.commit()
