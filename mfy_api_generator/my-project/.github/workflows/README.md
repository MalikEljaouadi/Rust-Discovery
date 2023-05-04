# Workflows

Workflows should have the following properties to be useful and trusted:

- **reproducible & consistent**: same inputs => same outputs (regardless of context, shared area,...),
- **fast**:
  - use shared area (between workflow's run, jobs, steps): caches (github-actions, oci/docker's images/layer), registry (oci/docker, nexus, nix....),
  - avoid redoing stuff (eg: compilation of dependencies, rebuild same image,...)

## CI

### Goals [`ci.yml`](./ci.yml)

- check & lint the code
- ensure no security issue into library dependencies
- run local tests (unit tests, local integration tests)
- build the package (oci/docker image) and publish it
- request deployment with the new image on dev cluster

### Debug

To debug the steps, sometimes it's easier to run them locally. A way to do it is to run the same docker image with the source code mounted and to execute commands interactively.

```sh
# davidb31/nix-on-debian:latest is the container image used in steps of ci.yml
docker run --rm -it \
  -v /var/run/docker.sock:/var/run/docker.sock:rw \
  -v $HOME/.aws:/root/.aws:ro \
  -v $PWD:/workspace \
  --workdir /workspace \
  --entrypoint sh \
  davidb31/nix-on-debian:latest
```

To check content of published oci image:

```sh
AWS_PROFILE=949225605787_ViewOnlyAccess aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin 949225605787.dkr.ecr.eu-central-1.amazonaws.com

# use dive from https://github.com/wagoodman/dive
# eg dive 949225605787.dkr.ecr.eu-central-1.amazonaws.com/acc-api@sha256:15c433a8efd74e1b996109d32c6d7010d5fb828da6a5214db92bbe7bc7e8c9fe
dive 949225605787.dkr.ecr.eu-central-1.amazonaws.com/....
```

### Setup

By default, git changes applied by github-action (with default `GITHUB_TOKEN`), could not trigger workflow.

> When you use the repository's GITHUB_TOKEN to perform tasks on behalf of the GitHub Actions app, events triggered by the GITHUB_TOKEN will not create a new workflow run. This prevents you from accidentally creating recursive workflow runs.

As a workaround (eg to trigger deployment), we follow the tips of [Trigger another GitHub Workflow — without using a Personal Access Token | > prompt](https://medium.com/prompt/trigger-another-github-workflow-without-using-a-personal-access-token-f594c21373ef), instead of using a personal access token [as suggested in doc](https://docs.github.com/en/actions/reference/events-that-trigger-workflows#triggering-new-workflows-using-a-personal-access-token)

1. create & register a secret & Deploy key into the repository (can also be done web UI)

    ```sh
    ssh-keygen -t ed25519 -f id_ed25519 -N "" -q -C ""
    gh repo deploy-key add id_ed25519.pub -t "COMMIT_KEY" --allow-write
    cat id_ed25519 | gh secret set "COMMIT_KEY" --app actions
    rm id_ed25519.pub id_ed25519
    ```

2. check that `ci.yml` use `COMMIT_KEY` (and git) to checkout in the job that should trigger an other workflow

Links:

- [Events that trigger workflows - GitHub Docs](https://docs.github.com/en/actions/reference/events-that-trigger-workflows#triggering-new-workflows-using-a-personal-access-token)
- [Github actions workflow not triggering with tag push - Code to Cloud / GitHub Actions - GitHub Support Community](https://github.community/t/github-actions-workflow-not-triggering-with-tag-push/17053)
- [Trigger another GitHub Workflow — without using a Personal Access Token | > prompt](https://medium.com/prompt/trigger-another-github-workflow-without-using-a-personal-access-token-f594c21373ef)
- [Triggering a new workflow from another workflow - Code to Cloud / GitHub Actions - GitHub Support Community](https://github.community/t/triggering-a-new-workflow-from-another-workflow/16250)

## Deployment

### Goals [`deployment.yml`](./deployment.yml)

- deploy the package on the cluster(s)
- be gitOps's friendly (in pull mode)
- reproducible deployment (by storying a maximum of )
- no need to rebuild the package (bake) for each deployment's destination
- only deploy to `*-stg` or `*-pro` from the `master`(or `main`) branch (`*-dev` from PR or `master`) to because in pro (or stg) deployed code (image,...) should come from a identified commit (commits in PR and other branches can be squashed).

### How

- all deployment information (manifest, configuration, version,...) are available as file into a git repository (eg under `/devops` folder of the current folder), so no variable issued from a "previous step" or context (except the destination cluster, namespace,...)
- deployment are triggered by git tag.
  - the git tag provide the target destination via the format `cluster/<cluster_name>`
  - the git tag is mobile along the git history, and the branch

### Commands

```sh
# list all deployable commit (some squashed commit could contains the commit)
git log --all --grep='^:bookmark:'

# the requested version for cluster ai-dev
git show -q "cluster/ai-dev"


# request deploy of a commit to cluster ai-dev
git tag "cluster/ai-dev" 622d5355688949b4f21d6f0b3b240846b4632383 --force
git push --tags --force

# to list all tags plus info
git checkout master
git pull --tags --force
git tag --format="%(refname:short)%09%(objectname:short)%09%(authordate)%09%(authorname)%09%(subject)"

# promote a deployment from ai-stg to ai-pro (to do on uptodate local code `git pull --tags --force`)
git tag "cluster/ai-pro" "cluster/ai-stg" --force
git tag --format="%(refname:short)%09%(objectname:short)%09%(authordate)%09%(authorname)%09%(subject)"
git push --tags --force
```

To see history you can also use github-actions web UI, by filtering by branch (includes tags), with url like `https://github.com/uberforcede/${repo_name}/actions?query=branch%3Acluster%2F${cluster_name}`, eg for [cluster-ai on wefox-ai-acc-api](https://github.com/uberforcede/wefox-ai-acc-api/actions?query=branch%3Acluster%2Fai-pro)

## Tips

- try to reduce number of oci images used to build
  - `davidb31/nix-on-debian:latest` to use general commands and nix environment (reproducible on local w/o docker).
  - `rust:1.59` xor `lukemathwalker/cargo-chef:latest-rust-1.59.0` (xor maybe in future `megalinter/megalinter-rust:v5`) as image to build rust code (in `ci` or in `Dockerfile`)
- try to build and test the code inside the `ci`, and to only COPY the result into an oci/docker image, to avoid duplicate build (of code and dependencies). If you switch to build inside docker, use multi-stage and
[cargo-chef](https://crates.io/crates/cargo-chef) for rust project.

## Troubleshot

- run of oci image failed with `standard_init_linux.go:228: exec user process caused: no such file or directory`. It can be caused by:
  - CMD is a shell script launched with wrong encoding (try tools like `dos2unix`)
  - CMD is an executable incompatible for the target platform (x86_64 or arm64,...)
  - CMD has a missing linked library (libc path, version, glibc vs musl,...)
