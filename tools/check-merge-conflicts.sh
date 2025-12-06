#!/usr/bin/env bash

set -eou pipefail

gitdir=$(git rev-parse --git-dir)
# if we aren't actively merging, there's no reason to check for conflict artifacts
if [[ ! -f "${gitdir}/MERGE_MSG" && ! -f "${gitdir}/MERGE_HEAD" && ! -f "${gitdir}/rebase-apply" && ! -f "${gitdir}/rebase-merge" ]]; then
	exit 0
fi

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
pushd "${SCRIPT_DIR}" > /dev/null || exit 1
pushd "$(git rev-parse --show-toplevel)" > /dev/null || exit 1

. tools/.library.sh

if [[ $# -eq 0 ]]; then
	FILES=$(git_files | xargs)
else
	FILES=$*
fi

patterns=( \
    "<<<<<<<"\
    "======="\
    ">>>>>>>" \
)

exit_code=0
for fn in ${FILES}; do
	for pattern in "${patterns[@]}"; do
		set +e
		error=$(grep "${pattern}" "${fn}" 2>&1 > /dev/null)
		set -e
		if [[ -n "${error}" ]]; then
			printf "%s may have merge conflict artifacts\n\t%s\n" "${fn}" "${error}"
			exit_code=1
			break
		fi
	done
done

popd > /dev/null || exit 1
popd > /dev/null || exit 1
exit "${exit_code}"
