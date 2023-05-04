#! /usr/bin/env bash

set -euo pipefail
# set -x
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
IMAGE="oxsecurity/megalinter:v6"

if podman --version >/dev/null 2>&1; then
  podman run --pull always --rm -it -v "${SCRIPT_DIR}:/tmp/lint:rw" "$IMAGE"
elif nerdctl --version >/dev/null 2>&1; then
  nerdctl run --pull always --rm -it -v "${SCRIPT_DIR}:/tmp/lint:rw" "$IMAGE"
elif docker --version >/dev/null 2>&1; then
  docker run --pull always --rm -it -v /var/run/docker.sock:/var/run/docker.sock:rw -v "${SCRIPT_DIR}:/tmp/lint:rw" "$IMAGE"
else
  echo "runner not found: podman or nerdctl or docker"
  exit 1
fi
