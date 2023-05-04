# syntax=docker/dockerfile:1.4

# This dockerfile build executable from source code before create the final image
# - use cargo-chef to cache build of dependencies into docker's layer
# - using this dockerfile into ci, do NOT require to provide the executable (steps could be remove, but more time will be needed)

ARG DEVCONTAINER_IMAGE=rust:1.68.0
ARG APP_NAME="appname_notset"

# checkov:skip=CKV_DOCKER_7:Ensure the base image uses a non latest version tag
# hadolint ignore=DL3006
FROM ${DEVCONTAINER_IMAGE} AS planner
WORKDIR /workspace

# hadolint ignore=SC2174
RUN mkdir -p -m 0700 ~/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts


# use of cargo chef ?
COPY . .
RUN --mount=type=ssh cargo chef prepare --recipe-path recipe.json

# checkov:skip=CKV_DOCKER_7:Ensure the base image uses a non latest version tag
# hadolint ignore=DL3006
FROM ${DEVCONTAINER_IMAGE} AS builder
WORKDIR /workspace

ARG AWS_SESSION_TOKEN \
  AWS_SECRET_ACCESS_KEY \
  AWS_ACCESS_KEY_ID \
  APP_NAME

ENV RUSTC_WRAPPER="sccache" \
  CARGO_INCREMENTAL=false \
  SCCACHE_BUCKET="wefox-ai-wai-sccache-dev" \
  SCCACHE_REGION="eu-central-1" \
  SCCACHE_S3_USE_SSL=true \
  SCCACHE_S3_KEY_PREFIX="$APP_NAME"

# hadolint ignore=SC2174
RUN mkdir -p -m 0700 ~/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts

COPY --from=planner /workspace/recipe.json recipe.json
# Build dependencies - this is the caching Docker layer!
RUN --mount=type=ssh \
  sccache --start-server && \
  cargo chef cook --release --recipe-path recipe.json && \
  sccache --stop-server

# Build application
COPY . .
RUN --mount=type=ssh \
  sccache --start-server && \
  cargo build --release && \
  sccache --stop-server

# We do not need the Rust toolchain to run the binary!

# To have the digest (instead of tag):
# - docker pull gcr.io/distroless/cc:nonroot | grep digest
# - or go to https://console.cloud.google.com/gcr/images/distroless/global/cc and filter by tags
FROM gcr.io/distroless/cc:nonroot AS ms

USER nonroot

ARG APP_NAME
ARG APP_VERSION="0.0.0"

# An environment variable could also be seen from inside the container as well during run.
ENV APP_NAME="$APP_NAME"
ENV APP_VERSION="$APP_VERSION"
ENV OTEL_SERVICE_NAME="$APP_NAME"

COPY --from=builder /workspace/target/release/my_project /app

ENV APP_PORT=8080
EXPOSE $APP_PORT
HEALTHCHECK NONE

ENTRYPOINT ["/app"]
