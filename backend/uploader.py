import yaml
from fastapi import UploadFile
from kubernetes import client, config, utils
from kubernetes.client.rest import ApiException
from tempfile import NamedTemporaryFile

# Load Kubernetes config
config.load_kube_config()

def handle_upload(file: UploadFile):
    try:
        # Save file to temporary location
        with NamedTemporaryFile(delete=False, suffix=".yaml") as tmp:
            tmp.write(file.file.read())
            tmp_path = tmp.name

        # Apply the YAML using Kubernetes utils
        k8s_client = client.ApiClient()
        utils.create_from_yaml(k8s_client, tmp_path)

        return {"status": "success", "message": "YAML applied successfully."}

    except ApiException as e:
        return {"status": "error", "message": f"Kubernetes API error: {e}"}
    except yaml.YAMLError as e:
        return {"status": "error", "message": f"YAML parsing error: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Unexpected error: {str(e)}"}
