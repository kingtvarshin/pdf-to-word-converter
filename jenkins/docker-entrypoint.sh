#!/bin/bash
# =============================================================================
# Jenkins Docker entrypoint
#
# Runs as root at container startup to match the Docker socket GID on the host,
# then drops privileges back to the jenkins user before starting Jenkins.
#
# This prevents "permission denied" errors when the docker group GID inside the
# image doesn't match the GID of /var/run/docker.sock on the host (TrueNAS).
# =============================================================================
set -e

SOCK=/var/run/docker.sock

if [ -S "$SOCK" ]; then
    HOST_GID=$(stat -c '%g' "$SOCK")

    if [ "$HOST_GID" = "0" ]; then
        # Socket owned by root group — make it accessible to all users
        chmod 666 "$SOCK"
        echo "[entrypoint] Docker socket owned by root — applied chmod 666"
    else
        # Find or create a group matching the host GID, then add jenkins to it
        if getent group "$HOST_GID" > /dev/null 2>&1; then
            GROUP_NAME=$(getent group "$HOST_GID" | cut -d: -f1)
            echo "[entrypoint] Found existing group '$GROUP_NAME' (GID $HOST_GID) — adding jenkins"
        else
            # Reassign the docker group GID to match the host
            groupmod -g "$HOST_GID" docker
            GROUP_NAME=docker
            echo "[entrypoint] Adjusted docker group GID to $HOST_GID"
        fi
        usermod -aG "$GROUP_NAME" jenkins
    fi
else
    echo "[entrypoint] WARNING: $SOCK not found — Docker commands will fail inside pipelines"
fi

# Drop to the jenkins user and start Jenkins normally
exec gosu jenkins /usr/local/bin/jenkins.sh "$@"
