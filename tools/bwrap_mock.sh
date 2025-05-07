#!/bin/sh

set -f

for last in "$@"; do :; done
COMMAND="$(realpath "$last" 2>/dev/null)"

case "$COMMAND" in
    */glycin-loaders/* )
        exec "$COMMAND"
        ;;
esac

IFS=":"
MOCK_BWRAP="$0"
MOCK_BWRAP_NAME="$(basename "$MOCK_BWRAP")"
if [ "$MOCK_BWRAP_NAME" = "bwrap" ]; then
    MOCK_BWRAP_DIR="$(dirname "$MOCK_BWRAP")"
    for p in $PATH; do
        if [ "${p%/}" = "${MOCK_BWRAP_DIR%/}" ] || [ "$(realpath "$p")" = "$(realpath "$MOCK_BWRAP_DIR")" ]; then
            continue
        fi
        FILTERED_PATH=${FILTERED_PATH:+${FILTERED_PATH}${IFS}}${p}
    done
fi

REAL_BWRAP="$(PATH="$FILTERED_PATH" command -v bwrap)"
if [ -z "$REAL_BWRAP" ] || [ "$(realpath "$REAL_BWRAP")" = "$(realpath "$MOCK_BWRAP")" ]; then
    echo "$0: Cannot find real bwrap"
    exit 1
fi

exec "$REAL_BWRAP" "$@"
