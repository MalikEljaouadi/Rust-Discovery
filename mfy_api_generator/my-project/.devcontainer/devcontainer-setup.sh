#!/bin/sh

set -e
# set -x

export DEBIAN_FRONTEND=noninteractive

# Install dependencies
apt-get update
apt-get install -y \
  bash \
  curl \
  jq \
  git \
  unzip \
  time \
  gettext \
  protobuf-compiler \
  ca-certificates \
  gnupg \
  lsb-release \
  groff less # required by awscli

# Install docker
# from https://docs.docker.com/engine/install/debian/
#shellcheck disable=SC2174
mkdir -m 0755 -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list >/dev/null
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
# docker --version

# Clean up
time rm -rf /var/lib/apt/lists

# Install just
curl --proto '=https' -sSf https://just.systems/install.sh | bash -s -- --to /usr/bin
just --version

# Install brew
# sh -c "$(curl -fsSL https://raw.githubusercontent.com/Linuxbrew/install/master/install.sh)"

# Install awscli v2
# brew install awscli
curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip -q awscliv2.zip
./aws/install
aws --version

# Install protoc (via apt-get)
# curl -fsSL "https://github.com/protocolbuffers/protobuf/releases/download/v3.15.8/protoc-3.15.8-linux-x86_64.zip" -o "protoc.zip"
# unzip protoc.zip -d /usr
# rm protoc.zip
protoc --version # Ensure compiler version is 3+

# Install Rust complementary tool
rustup --version
# see [Installation instructions outdated · Issue #3271 · rust-lang/rustfmt](https://github.com/rust-lang/rustfmt/issues/3271)
# without explicit toolchain `cargo fmt --all -- --check` failed with
# ```
# error: 'cargo-fmt' is not installed for the toolchain '1.68-x86_64-unknown-linux-gnu'
# ```
# RUST_TOOLCHAIN="${RUST_VERSION}-x86_64-unknown-linux-gnu"
# rustup toolchain remove "${RUST_TOOLCHAIN}" && rustup toolchain install "${RUST_TOOLCHAIN}"
rustup toolchain list
rustup component add clippy rustfmt
# rustup component add rustfmt --toolchain 1.68-x86_64-unknown-linux-gnu
cargo --version
cargo clippy --version
cargo fmt --version

# Install sccache
SCCACHE_VERSION=0.4.2 #0.3.3
curl -fsSL "https://github.com/mozilla/sccache/releases/download/v$SCCACHE_VERSION/sccache-v$SCCACHE_VERSION-x86_64-unknown-linux-musl.tar.gz" | tar -xz
mv "sccache-v$SCCACHE_VERSION-x86_64-unknown-linux-musl/sccache" /usr/bin/sccache
chmod +x /usr/bin/sccache
rm -Rf "sccache-v$SCCACHE_VERSION-x86_64-unknown-linux-musl"

# Install cargo-chef
# cargo install cargo-chef # build can take 2min, that affect pre-built and deploy
curl -fsSL https://github.com/LukeMathWalker/cargo-chef/releases/download/v0.1.52/cargo-chef-x86_64-unknown-linux-musl.tar.gz | tar -xz
mv cargo-chef /usr/bin/cargo-chef
chmod +x /usr/bin/cargo-chef
