FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git=1:2.34.1-1ubuntu1.9 \
        python3.11=3.11.* \
        python3.11-venv=3.11.* \
        nodejs=18.* \
        nsjail \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/usr/bin/python3.11:$PATH"
CMD ["/bin/bash"]
