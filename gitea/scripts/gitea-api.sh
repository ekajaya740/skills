#!/usr/bin/env bash
# gitea-api.sh — helper for Gitea REST API calls
# Usage: source this file, then: gitea_api_get <instance> <endpoint>
#
# Instance token is read from ~/.hermes/gitea/<instance>
# Instance token env override: GITEA_TOKEN_<INSTANCE_UPPERCASE>
# Instance base URL env override: GITEA_BASE_URL_<INSTANCE_UPPERCASE>

gitea_api_get() {
    local INSTANCE="$1"
    local ENDPOINT="$2"

    if [ -z "$INSTANCE" ] || [ -z "$ENDPOINT" ]; then
        echo "Usage: gitea_api_get <instance> <endpoint>" >&2
        return 1
    fi

    local TOKEN_FILE="$HOME/.hermes/gitea/$INSTANCE"
    local TOKEN=""

    # 1. Check env override
    local ENV_TOKEN_VAR="GITEA_TOKEN_${INSTANCE^^}"
    if [ -n "${!ENV_TOKEN_VAR}" ]; then
        TOKEN="${!ENV_TOKEN_VAR}"
    elif [ -f "$TOKEN_FILE" ]; then
        TOKEN="$(cat "$TOKEN_FILE" | tr -d '[:space:]')"
    fi

    if [ -z "$TOKEN" ]; then
        echo "Error: No token found for instance '$INSTANCE'. Checked: $TOKEN_FILE and env ${ENV_TOKEN_VAR}" >&2
        return 1
    fi

    # Base URL
    local BASE="https://code.re-creation.co.jp"
    local ENV_BASE_VAR="GITEA_BASE_URL_${INSTANCE^^}"
    if [ -n "${!ENV_BASE_VAR}" ]; then
        BASE="${!ENV_BASE_VAR}"
    fi

    # Clean endpoint (ensure leading /)
    case "$ENDPOINT" in
        /) ;;
        /*) ;;
        *) ENDPOINT="/$ENDPOINT" ;;
    esac

    curl -s -H "Authorization: token ${TOKEN}" "${BASE}/api/v1${ENDPOINT}"
}
