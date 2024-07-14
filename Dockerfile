ARG BUILDPLATFORM=linux/amd64
ARG BASE_IMAGE="binhex/arch-base"

FROM --platform=${BUILDPLATFORM} ${BASE_IMAGE} as cosmovisor

# Install dependencies
RUN pacman -Syyu --noconfirm \
    aria2 \
    dropbear \
    musl \
    python-lz4 \
    python-pip \
    python-yaml \
    python-tomlkit \
    python-requests \
    python-fastapi \
    python-dnspython \
    python-boto3 \
    skopeo \
    tmux \
    uvicorn \
    vim \
    wget
# install grpcurl and schedule
RUN set -eux && \
    curl -sSL https://github.com/fullstorydev/grpcurl/releases/download/v1.8.8/grpcurl_1.8.8_linux_$(uname -m).tar.gz | \
    tar -xz -C /usr/local/bin/ grpcurl && \
    rm /usr/lib/python3.12/EXTERNALLY-MANAGED && \
    pip install schedule

COPY --from=ghcr.io/binaryholdings/cosmprund:v1.0.0 /usr/bin/cosmprund /usr/local/bin/cosmprund
COPY ./etc /etc/
COPY ./bin/* /usr/local/bin/

# set permissions and create user
RUN set -eux && \
    chmod +x /usr/local/bin/* && \
    groupadd -g 1000 cosmovisor && \
    useradd -u 1000 -g 1000 -s /bin/bash -Md /app cosmovisor 

WORKDIR /app
ENTRYPOINT [ "/usr/local/bin/entrypoint.sh" ]
CMD [ "supervisord", "-c", "/etc/supervisord.conf" ]
