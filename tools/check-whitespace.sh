#!/usr/bin/env bash

set -eou pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
pushd "${SCRIPT_DIR}" > /dev/null || exit 1
pushd "$(git rev-parse --show-toplevel)" > /dev/null || exit 1

. tools/.library.sh

if [[ $# -eq 0 ]]; then
	FILES=$(git_files | xargs)
else
	FILES=$*
fi

TO_FIX=()
exit_code=0
set +e
for fn in ${FILES}; do
	found=$(grep -l ' +$' "${fn}")
	if [[ -n "${found}" ]]; then
		TO_FIX+=("${found}")
		exit_code=1
	fi
done
set -e

if [[ "${#TO_FIX[@]}" -gt 0 ]]; then
	printf '%s\n' "${TO_FIX[@]}"
fi
popd > /dev/null || exit 1
popd > /dev/null || exit 1
exit "${exit_code}"
