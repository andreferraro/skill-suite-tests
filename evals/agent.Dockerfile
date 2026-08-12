FROM mcr.microsoft.com/playwright:v1.62.1-noble

ARG CODEX_VERSION=0.147.0
ARG CURSOR_VERSION=2026.08.11-e8db854
ARG CURSOR_SHA256=bfff4bf6f4e9dd30c1d0ef0a70b6077b074015dd2948e4c50685d53afdcfce5a

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        python-is-python3 \
        python3 \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN npm install --global "@openai/codex@${CODEX_VERSION}"
RUN curl -fsSL \
        "https://downloads.cursor.com/lab/${CURSOR_VERSION}/linux/x64/agent-cli-package.tar.gz" \
        -o /tmp/cursor-agent.tar.gz \
    && echo "${CURSOR_SHA256}  /tmp/cursor-agent.tar.gz" | sha256sum --check --strict \
    && mkdir -p /opt/cursor-agent \
    && tar --strip-components=1 -xzf /tmp/cursor-agent.tar.gz -C /opt/cursor-agent \
    && rm /tmp/cursor-agent.tar.gz \
    && ln -s /opt/cursor-agent/cursor-agent /usr/local/bin/cursor-agent

WORKDIR /workspace
