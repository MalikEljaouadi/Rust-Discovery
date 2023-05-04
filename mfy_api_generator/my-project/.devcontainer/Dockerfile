# syntax=docker/dockerfile:1.4

# the value should be aligned with the content of rust-toolchain.toml
# else some strange error like
# ```
# error: 'cargo-fmt' is not installed for the toolchain 'xxxx-x86_64-unknown-linux-gnu'
# ```
ARG RUST_VERSION=1.68.0

FROM rust:${RUST_VERSION} as devcontainer

# Versions
ARG HELM_VERSION=3.11.1
ARG KUBECTL_VERSION=1.24.0
ARG RUST_VERSION

# change this value to invalidate cache of layer and force docker/podman/... to rebuild following layer
ARG FORCE_REBUILD=202303161830

# Copies your code file from your action repository to the filesystem path `/` of the container
# TODO import content of devcontainer as RUN command to be able to use cache of layer
COPY devcontainer-setup.sh /devcontainer-setup.sh
RUN /devcontainer-setup.sh

# from https://docs.github.com/en/actions/creating-actions/dockerfile-support-for-github-actions
# - Docker actions must be run by the default Docker user (root)

ENTRYPOINT ["bash"]
