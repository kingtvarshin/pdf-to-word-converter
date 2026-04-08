# Custom Jenkins image with Docker CLI included.
# This lets the Jenkins pipeline run "docker build/push" commands by using
# the host Docker daemon via the mounted /var/run/docker.sock socket.

FROM jenkins/jenkins:lts-jdk17

USER root

# Install Docker CLI (no daemon — uses the host socket)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gnupg \
        lsb-release && \
    install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg \
        | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    chmod a+r /etc/apt/keyrings/docker.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
        https://download.docker.com/linux/debian $(lsb_release -cs) stable" \
        > /etc/apt/sources.list.d/docker.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends docker-ce-cli && \
    rm -rf /var/lib/apt/lists/*

# Allow the jenkins user to talk to the Docker socket
RUN groupadd -f docker && usermod -aG docker jenkins

USER jenkins

# Skip the Jenkins setup wizard on first boot
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"
