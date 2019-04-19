#!/bin/bash

pushd () {
    command pushd "$@" > /dev/null
}

popd () {
    command popd "$@" > /dev/null
}

success_expected='{"result":[{"ci":{"errors":false}},{"file_config":{"errors":false}},{"pi_style_pipe_vars":{"errors":false}},{"pi_validate_pipe_vars":{"errors":false}}]}'
missing_stage_expected=$(cat <<EOF
{"result":[{"ci":{"errors":[{"include":{"errors":false}},{"stages":{"errors":"{'stages': [ValueError(\"Stages must include validate. You passed ['lint', 'build', 'generate_docker_image_push_to_nexus']\")]}"}}]}},{"file_config":{"errors":false}},{"pi_style_pipe_vars":{"errors":false}},{"pi_validate_pipe_vars":{"errors":false}}]}
EOF
)
disable_pipe_expected=$(cat <<EOF
{"result":[{"ci":{"errors":false}},{"file_config":{"errors":false}},{"pi_style_pipe_vars":{"errors":"{'pi_style_pipe_vars': {'run_pipe': ['Style Pipe must be enabled. You supplied False']}}"}},{"pi_validate_pipe_vars":{"errors":false}}]}
EOF
)
invalid_styler_expected=$(cat <<EOF
{"result":[{"ci":{"errors":false}},{"file_config":{"errors":"{'file_config': {30: {'styler': [ValueError(\"File styler must be one of ['noop', 'cpplint', 'flake8']. You passed hello\")]}}}"}},{"pi_style_pipe_vars":{"errors":false}},{"pi_validate_pipe_vars":{"errors":false}}]}
EOF
)
invalid_project_expected=$(cat <<EOF
{"result":[{"repo":{"errors":"No project named invalidin https://github.com/AFCYBER-DREAM/piedpiper-project-validations.git"}}]}
EOF
)


errors=0
for project in \
    success \
	invalid_project \
	disable_pipe \
	missing_stage; do


    echo "Running tests on project $project in $(dirname $0)/$project"
	pushd $(dirname $0)
	if [[ -f "${project}.zip" ]]; then
	  echo "Removing leftover zipfile ${project}.zip"
	  rm -f "${project}.zip"
	fi
	pushd "${project}"
    zip -qr ../"${project}".zip *
	popd
	results=$(curl -s -F "files=@${project}.zip" http://127.0.0.1:8080/function/piedpiper-validator-function)
	expected=${project}_expected
	if [[ "${results}" != "${!expected}" ]]; then
	  echo "Results do not match expected results."
	  echo "Results: ${results}"
	  echo "Expected: ${!expected}"
	  errors=$((errors+1))
	fi
    if [[ -f "${project}.zip" ]]; then
      echo "Removing leftover zipfile ${project}.zip"
      rm -f "${project}.zip"
    fi
	popd
done

if [[ "${errors}" == 0 ]]; then
    echo "Tests ran successfully";
    exit 0;
else
    echo "Tests failed";
	exit 1;
fi
