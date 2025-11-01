#!/usr/bin/env bash

set -eou pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
pushd "${SCRIPT_DIR}" > /dev/null || exit 1
pushd "$(git rev-parse --show-toplevel)" > /dev/null || exit 1

. tools/.library.sh

if [[ $# -eq 0 ]]; then
	FILES=$(git_files | grep "json$" | xargs)
else
	FILES=$*
fi

exit_code=0
for fn in ${FILES}; do
	set +e
	error=$(jq '.' "${fn}" 2>&1 > /dev/null)
	set -e
	if [[ -n "${error}" ]]; then
		printf "Failure reading %s\n\t%s\n" "${fn}" "${error}"
		exit_code=1
	fi
done

popd > /dev/null || exit 1
popd > /dev/null || exit 1
exit "${exit_code}"
