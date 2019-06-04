from .util import request_new_task_id, call_validation_function, update_task_id_status
from .config import Config


def handle(request):
    """handle a request to the function
    Args:
        req (str): request body
    """
    gman_url = Config["gman"]["url"]

    try:
        run_id = request.get_json().get("run_id")
        project = request.get_json().get("project")
        client_task_id = request.get_json().get("task_id")
        artifacts = request.get_json().get("artifacts")
        configs = request.get_json().get("configs")
        stage = request.get_json().get("stage")

        internal_task_id = request_new_task_id(
            run_id=run_id,
            gman_url=gman_url,
            status="started",
            project=project,
            caller="validator_gateway",
        )
    except:
        message = "Failed to request new taskID from gman."
        update_task_id_status(
            gman_url=gman_url,
            task_id=client_task_id,
            status="failed",
            message=message,
            caller="validator_gateway",
        )
        return 500

    try:
        return_value = call_validation_function(
            run_id=run_id,
            faas_url="http://172.17.0.1:8080/async-function/piedpiper-validator-function",
            project=project,
            task_id=internal_task_id,
            configs=configs,
        )

        return_value.raise_for_status()
    except request.HTTPError as e:
        message = "There was an error calling the validation function. "
        update_task_id_status(
            gman_url=gman_url,
            task_id=internal_task_id,
            status="failed",
            message=message,
            caller="validator_gateway",
        )
        return 500
    if return_value.status_code == 202:
        update_task_id_status(
            gman_url=gman_url,
            task_id=internal_task_id,
            status="delegated",
            message="Delegated execution to validator executor",
            caller="validator_gateway",
        )
        return {"task_id": internal_task_id}
