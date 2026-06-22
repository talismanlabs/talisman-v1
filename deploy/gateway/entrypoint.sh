#!/bin/sh
# Render the nginx config, injecting the real provider keys read from MOUNTED secret files
# (ADR-0010). Reading from files (not -e env on the command line) keeps the keys out of the
# process table / `podman inspect`. The keys live only in this gateway — never in a worker.
set -eu

read_secret() {
    if [ ! -s "$1" ]; then
        echo "credential-gateway: secret file $1 is missing or empty" >&2
        exit 1
    fi
    tr -d '\r\n' <"$1"
}

ANTHROPIC_API_KEY="$(read_secret /run/secrets/anthropic_api_key)"
OPENAI_API_KEY="$(read_secret /run/secrets/openai_api_key)"
export ANTHROPIC_API_KEY OPENAI_API_KEY

envsubst '${ANTHROPIC_API_KEY} ${OPENAI_API_KEY}' \
    </etc/nginx/nginx.conf.template >/etc/nginx/nginx.conf

exec nginx -g 'daemon off;'
