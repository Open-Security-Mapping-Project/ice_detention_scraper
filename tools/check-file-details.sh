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
SHEBANG_FIXED=()
WHITESPACE_TO_FIX=()
# default to 5 MB
FILE_SIZE=${FILE_SIZE:-5000000}
TOO_BIG=()
exit_code=0

for fn in ${FILES}; do
	set +e
	shebang=$(grep -l "^#!/" "${fn}")
	if [[ -n "${shebang}" && ! -x "${fn}" ]]; then
		chmod +x "${fn}"
		SHEBANG_FIXED+=("${fn}")
		exit_code=1
	fi
	set +e
	# grep exits non-0 when it doesn't find anything
	whitespace=$(grep -l ' +$' "${fn}")
	set -e
	if [[ -n "${whitespace}" ]]; then
		WHITESPACE_TO_FIX+=("${whitespace}")
		exit_code=1
	fi
	size=$(stat --printf="%s" "${fn}")
	if [[ "${size}" -gt "${FILE_SIZE}" ]]; then
		TOO_BIG+=("${fn}: ${size}")
		exit_code=1
	fi
done

if [[ "${#SHEBANG_FIXED[@]}" -gt 0 ]]; then
	echo "Fixed executable bit on:"
	printf '\t%s\n' "${SHEBANG_FIXED[@]}"
fi
if [[ "${#WHITESPACE_TO_FIX[@]}" -gt 0 ]]; then
	echo "Should clean whitespace on:"
	printf '\t%s\n' "${WHITESPACE_TO_FIX[@]}"
fi

if [[ "${#TOO_BIG[@]}" -gt 0 ]]; then
	echo "Files larger than ${FILE_SIZE}:"
	printf '\t%s\n' "${TOO_BIG[@]}"
fi

popd > /dev/null || exit 1
popd > /dev/null || exit 1
exit "${exit_code}"
