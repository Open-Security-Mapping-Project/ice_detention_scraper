#!/usr/bin/env bash

set -eo pipefail
LC_ALL=C
export LC_ALL

function git_files {
	FILES=$(git ls-files --exclude-standard)
	FILES+=" $(git ls-files --exclude-standard --others)"
	echo "${FILES}"
}
