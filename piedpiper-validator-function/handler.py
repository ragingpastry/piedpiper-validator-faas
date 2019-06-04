import tempfile
import os
import git
import yaml
import traceback
from .util import (
    unzip_files,
    update_task_id_status,
    download_artifact,
    upload_artifact,
    read_secrets,
    nested_dict_iter,
    load_module_from_file,
)
from .config import Config

gman_url = Config["gman"]["url"]
storage_url = Config["storage"]["url"]


def handle(request):
    """handle a request to the function
    Args:
        req (str): request body
    """

    run_id = request.get_json().get("run_id")
    project_name = request.get_json().get("project")
    task_id = request.get_json()["task_id"]
    configs = request.get_json().get("configs")

    access_key = read_secrets().get("access_key")
    secret_key = read_secrets().get("secret_key")

    policy_version = next(config.get("policy_version") for config in configs)

    update_task_id_status(
        gman_url=gman_url,
        status="received",
        task_id=task_id,
        message="Received execution task from validator gateway",
        caller="validator_func",
    )

    validation_repo = (
        "https://github.com/AFCYBER-DREAM/piedpiper-project-validations.git"
    )

    validation_results = {}

    with tempfile.TemporaryDirectory() as temp_dir:
        download_artifact(
            run_id,
            "artifacts/python_project.zip",
            f"{temp_dir}/validation.zip",
            storage_url,
            access_key,
            secret_key,
        )
        unzip_files(f"{temp_dir}/validation.zip", temp_dir)

        with open(f"{temp_dir}/piedpiper.d/default/stages.yml") as f:
            stages = yaml.safe_load(f.read())
        with open(f"{temp_dir}/piedpiper.d/default/config.yml") as f:
            piedpiper_config = yaml.safe_load(f.read())
        with open(f"{temp_dir}/.gitlab-ci.yml") as f:
            ci_provider_config = yaml.safe_load(f.read())

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = git.Repo.clone_from(
                validation_repo, temp_dir, branch="refactor-picli"
            )

            if not os.path.isdir(f"{repo.working_tree_dir}/{project_name}"):
                validation_results.update(
                    {
                        "repo": {
                            "errors": f"No project named {project_name}"
                            f"in {validation_repo}"
                        }
                    }
                )
                return validation_results
            elif not os.path.isdir(
                f"{repo.working_tree_dir}/{project_name}/releases/{policy_version}"
            ):
                validation_results.update(
                    {
                        "repo": {
                            "errors": f"No release {policy_version}"
                            f"found in {validation_repo}"
                        }
                    }
                )
                return validation_results

            module_directory = (
                f"{repo.working_tree_dir}/{project_name}/" f"releases/{policy_version}/"
            )

            for item in ["stages", "config"]:
                module = load_module_from_file(
                    f"validate_{item}", f"{module_directory}/validate_{item}.py"
                )
                if item == "stages":
                    result = module.validate(stages["stages"])
                elif item == "config":
                    result = module.validate(piedpiper_config)
                if isinstance(result, Exception):
                    validation_results.update({item: {"errors": str(result.messages)}})
                else:
                    validation_results.update({item: {"errors": False}})

            # ci_result = False
            ci_results = {}
            ci_module = load_module_from_file(
                "pi_gitlab_ci", f"{module_directory}/pi_gitlab_ci/pi_gitlab_ci.py"
            )
            for ci_key, ci_value in ci_provider_config.items():
                if ci_key == "stages":
                    result = ci_module.validate(
                        ci_key.capitalize(), {"stages": ci_value}
                    )
                    if isinstance(result, Exception):
                        ci_results.update({ci_key: {"errors": str(result.messages)}})
                    else:
                        ci_results.update({ci_key: {"errors": False}})
                elif ci_key == "include":
                    temp_dict = {ci_key: ci_value}
                    result = ci_module.validate(ci_key.capitalize(), temp_dict)
                    if isinstance(result, Exception):
                        ci_results.update({ci_key: {"errors": str(result.messages)}})
                    else:
                        ci_results.update({ci_key: {"errors": False}})

            validation_results.update({"ci": ci_results})

    except Exception as e:
        validation_results.update(
            {"error": {"errors": f"{str(e)}\n\n{traceback.format_exc()}"}}
        )

    finally:
        temp_directory = tempfile.TemporaryDirectory()
        # Loop through validation results and ensure all values are False.
        if not any([value[1] for value in nested_dict_iter(validation_results)]):
            validation_results = "Validation completed successfully!"
        validation_log_file = f"{temp_directory.name}/validation.log"
        with open(validation_log_file, "w") as log_file:
            log_file.write(yaml.safe_dump(validation_results))
        upload_artifact(
            run_id,
            "artifacts/logs/validate/validation.log",
            validation_log_file,
            storage_url,
            access_key,
            secret_key,
        )
        update_task_id_status(
            gman_url=gman_url,
            task_id=task_id,
            status="completed",
            message="Validator execution complete",
            caller="validator_func",
        )
