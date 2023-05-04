#! /usr/bin/env bash

set -euo pipefail
# set -x
# SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

CLUSTER_BASENAME="$1"
TAG_PREFIX="cluster/${CLUSTER_BASENAME}"

pushd "$PROJECT_DIR"

git fetch origin --tags --force

echo "::group::git tag before:"
echo "-------------------------------------------"
git tag --format="::debug::%(refname:short)%09%(objectname:short)%09%(authordate)%09%(authorname)%09%(subject)"
echo "-------------------------------------------"
echo "::endgroup::"

NEXT_CLUSTER=""
if [[ $(git describe --tags --always --match="${TAG_PREFIX}-pro") == "${TAG_PREFIX}-pro" ]]; then
  echo "::notice::already top promoted to ${TAG_PREFIX}-pro"
  NEXT_CLUSTER=""
elif [[ $(git describe --tags --always --match="${TAG_PREFIX}-stg") == "${TAG_PREFIX}-stg" ]]; then
  NEXT_CLUSTER="${TAG_PREFIX}-pro"
elif [[ $(git describe --tags --always --match="${TAG_PREFIX}-dev") == "${TAG_PREFIX}-dev" ]]; then
  # TODO support hotfix branch
  # The reason behind using `git log` instead of `git branch master ...` is it still works
  # when the repo is fetched on a tag, not a branch.
  # shellcheck disable=SC2143
  if [[ -n $(git log origin/master | grep "$(git rev-parse HEAD)") ]]; then
    NEXT_CLUSTER="${TAG_PREFIX}-stg"
  else
    echo "::warning::only commit on 'master' branch can be promoted to ${TAG_PREFIX}-stg"
    NEXT_CLUSTER=""
  fi
else
  NEXT_CLUSTER="${TAG_PREFIX}-dev"
fi

if [[ -n "$NEXT_CLUSTER" ]]; then
  CURRENT=$(git describe --always --dirty --long --all)
  echo "::notice::promote $CURRENT to $NEXT_CLUSTER"
  git tag "$NEXT_CLUSTER" --force
  git push --tags --force
fi

echo "::group::git tag after:"
echo "-------------------------------------------"
echo "after:"
git tag --format="::notice::%(refname:short)%09%(objectname:short)%09%(authordate)%09%(authorname)%09%(subject)"
echo "-------------------------------------------"
echo "::endgroup::"

popd
