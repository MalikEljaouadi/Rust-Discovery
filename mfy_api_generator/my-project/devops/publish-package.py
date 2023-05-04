from ast import literal_eval
from pathlib import Path
import os
import subprocess
import shlex
import logging
import sys
import re
from typing import List, Optional

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_DIR = Path(__file__).parents[1].resolve()


def run_cmd(cmd: str) -> str:
    """Return the striped output of a command shell."""
    return subprocess.check_output(shlex.split(cmd), text=True).strip()


GIT_REVISION = run_cmd("git describe --always --dirty")


def getenv(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable and put default if empty string."""
    value = os.getenv(key, default)
    return value if value else default  # environment variable can be set but an empty string


def get_environment_config(**overrides: dict[str, str]) -> dict:
    """Return a dictionary with all the value needed to build the Dockerfile target and update values for deployment."""
    config = {
        "APP_NAME": getenv("APP_NAME", default=PROJECT_DIR.name),
        "APP_VERSION": getenv("APP_VERSION", default=GIT_REVISION),
        "DOCKERFILE": getenv("DOCKERFILE", default=str(SCRIPT_DIR / "Dockerfile")),
        "AWS_ACCOUNT_ID": os.getenv("AWS_ACCOUNT_ID"),
        "GITHUB_OUTPUT": getenv("GITHUB_OUTPUT", default="/dev/null"),
        "AWS_DEFAULT_REGION": os.getenv("AWS_DEFAULT_REGION"),
        "WEFOX_REGISTRY_PASSWORD": os.getenv("WEFOX_REGISTRY_PASSWORD"),
        "WEFOX_REGISTRY_USERNAME": os.getenv("WEFOX_REGISTRY_USERNAME"),
        "NPM_REGISTRY_URL": os.getenv("NPM_REGISTRY_URL"),
        "NPM_TOKEN": os.getenv("NPM_TOKEN"),
        "NEPTUNE_API_TOKEN": os.getenv("NEPTUNE_API_TOKEN"),
        "AWS_SESSION_TOKEN": os.getenv("AWS_SESSION_TOKEN"),
        "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY"),
        "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID"),
        "SSH_AUTH_SOCK": os.getenv("SSH_AUTH_SOCK"),
        "DEVCONTAINER_IMAGE": os.getenv('DEVCONTAINER_IMAGE'),
        "AWS_S3_CACHE_BUCKET": os.getenv("AWS_S3_CACHE_BUCKET"),
        **overrides,
    }

    config["IMAGE_TAG"] = getenv("IMAGE_TAG", default=config["APP_VERSION"])
    config["IMAGE_BASENAME"] = f"{config['APP_NAME']}-{config['app_target']}"

    if config["AWS_ACCOUNT_ID"] is None:
        config["ECR_REGISTRY"] = ""
        config["IMAGE_NAME"] = config["IMAGE_BASENAME"]
    else:
        config["ECR_REGISTRY"] = f"{config['AWS_ACCOUNT_ID']}.dkr.ecr.{config['AWS_DEFAULT_REGION']}.amazonaws.com"
        config["IMAGE_NAME"] = f"{config['ECR_REGISTRY']}/{config['IMAGE_BASENAME']}"

    config["IMAGE_FULL_TAG"] = f"{config['IMAGE_NAME']}:{config['IMAGE_TAG']}"
    config["IMAGE_DIGEST"] = ""

    cmd_builder_candidate = ["podman", "nerdctl", "docker"]

    config["CMD_BUILDER"] = None
    for cmd_builder in cmd_builder_candidate:
        try:
            cmd_result = run_cmd(f"{cmd_builder} --version")
        except:
            pass
        else:
            config["CMD_BUILDER"] = cmd_builder
            break

    if config["CMD_BUILDER"] is None:
        logging.error("builder not found: docker or nerdctl")
        exit(1)

    logging.info(f"builder is {cmd_result}")
    return config


def build_local_image(config: dict, push: bool = False):
    """Build the docker image and push it on the ecr registry if push is True."""
    cmd_builder = config["CMD_BUILDER"]

    opts = ""

    if push:
        opts += " --output=type=image,push=true"

    if config['AWS_DEFAULT_REGION'] and config['AWS_S3_CACHE_BUCKET']:
        cache_s3_prefix=run_cmd("date +'%Y-%m'")
        cache=f"type=s3,region={config['AWS_DEFAULT_REGION']},bucket={config['AWS_S3_CACHE_BUCKET']},prefix={cache_s3_prefix}"
        opts += f" --cache-from={cache} --cache-to={cache}"

        if cmd_builder == "docker":
            run_cmd("docker buildx create --driver docker-container --driver-opt image=moby/buildkit:master,network=host --use")
            run_cmd("docker buildx inspect --bootstrap")

    if config['SSH_AUTH_SOCK']:
        opts += f" --ssh \"default={config['SSH_AUTH_SOCK']}\""

    if config['DEVCONTAINER_IMAGE']:
        opts += f" --build-arg \"DEVCONTAINER_IMAGE={config['DEVCONTAINER_IMAGE']}\""


    if cmd_builder == "docker":
        cmd_builder = f"{cmd_builder} buildx"

    logging.info(f"'{config['IMAGE_FULL_TAG']}' build")

    image_source = run_cmd("git config remote.origin.url")
    created = run_cmd("date -Iminutes")

    full_cmd = (
        f"{cmd_builder} build "
        "--progress=plain "
        "--platform=linux/amd64 "
        f"{opts} "
        f'--target "{config["app_target"]}" '
        f'--label "org.opencontainers.image.source={image_source})" '
        f'--label "org.opencontainers.image.revision={GIT_REVISION}" '
        '--label "org.opencontainers.image.vendor=com.wefox" '
        f'--label "org.opencontainers.image.base.name={config["IMAGE_FULL_TAG"]}" '
        f'--label "org.opencontainers.image.created={created}" '
        f'--label "com.wefox.app.name={config["APP_NAME"]}" '
        f'--label "com.wefox.app.version={config["APP_VERSION"]}" '
        '--build-arg "BUILDKIT_INLINE_BUILDINFO_ATTRS=1" '
        f'--build-arg "APP_NAME={config["APP_NAME"]}" '
        f'--build-arg "APP_VERSION={config["APP_VERSION"]}" '
        f'--build-arg "WEFOX_REGISTRY_PASSWORD={config["WEFOX_REGISTRY_PASSWORD"]}" '
        f'--build-arg "WEFOX_REGISTRY_USERNAME={config["WEFOX_REGISTRY_USERNAME"]}" '
        f'--build-arg "NPM_REGISTRY_URL={config["NPM_REGISTRY_URL"]}" '
        f'--build-arg "NPM_TOKEN={config["NPM_TOKEN"]}" '
        f'--build-arg "NEPTUNE_API_TOKEN={config["NEPTUNE_API_TOKEN"]}" '
        f'--build-arg "AWS_SESSION_TOKEN={config["AWS_SESSION_TOKEN"]}" '
        f'--build-arg "AWS_SECRET_ACCESS_KEY={config["AWS_SECRET_ACCESS_KEY"]}" '
        f'--build-arg "AWS_ACCESS_KEY_ID={config["AWS_ACCESS_KEY_ID"]}" '
        f'-t "{config["IMAGE_FULL_TAG"]}" '
        f'-f "{config["DOCKERFILE"]}" '
        f"{PROJECT_DIR}"
    ).replace("None", "")

    run_cmd(full_cmd)


def build_ecr_image(config: dict[str, str]):
    """Connect and init ECR repository on AWS then build and push the docker image on it."""
    login_part1 = subprocess.Popen(
        shlex.split(f"aws ecr get-login-password --region {config['AWS_DEFAULT_REGION']}"), stdout=subprocess.PIPE
    )

    login_part2 = (
        subprocess.run(
            shlex.split(f'{config["CMD_BUILDER"]} login --username AWS --password-stdin "{config["ECR_REGISTRY"]}"'),
            stdin=login_part1.stdout,
            capture_output=True,
        )
        .stdout.decode("utf8")
        .strip()
    )

    logging.info(login_part2)

    cmd = (
        f"aws ecr describe-images --repository-name {config['IMAGE_BASENAME']} --region {config['AWS_DEFAULT_REGION']} "
        '--query "sort_by(imageDetails,& imagePushedAt)[ * ].imageTags[ * ]"'
    )
    images = subprocess.run(shlex.split(cmd), capture_output=True).stdout.decode("utf8").strip()
    # return '[]' when empty else something like'[\n    [\n        "1489599"\n    ]\n]'

    logging.debug(f"{images=}")

    if (not images) or (not eval(images)):
        logging.info(f"create ecr repository '{config['IMAGE_BASENAME']}'")
        run_cmd(
            f'aws ecr create-repository --repository-name "{config["IMAGE_BASENAME"]}" '
            f'--region "{config["AWS_DEFAULT_REGION"]}"'
        )

    if re.search(config["IMAGE_TAG"], images) is None:
        logging.info(f"'{config['IMAGE_FULL_TAG']}' not found on ecr")
        build_local_image(config=config, push=True)
    else:
        logging.info(f"'{config['IMAGE_FULL_TAG']}' found on ecr: nothing to do")

    run_cmd(f"{config['CMD_BUILDER']} logout {config['ECR_REGISTRY']}")


def update_image_into_file(config: dict):
    """Update the `values.yaml` file with the value of the new Docker image."""
    target_file = PROJECT_DIR / config["values_file_path"]
    if target_file and target_file.exists():
        with open(target_file, "r") as fopen:
            content = fopen.read()
        content = re.sub(
            rf"\".*?\" # ?{config['app_target']}\.image_name",
            f"\"{config['IMAGE_NAME']}\" # {config['app_target']}.image_name",
            content,
        )
        content = re.sub(
            rf"\".*?\" # ?{config['app_target']}\.image_tag",
            f"\"{config['IMAGE_TAG']}\" # {config['app_target']}.image_tag",
            content,
        )
        content = re.sub(
            rf"\".*?\" # ?{config['app_target']}\.image_digest",
            f"\"{config['IMAGE_DIGEST']}\" # {config['app_target']}.image_digest",
            content,
        )

        with open(target_file, "w") as fopen:
            fopen.write(content)

def set_github_output(name, value):
    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        print(f'{name}={value}', file=fh)

def main():
    app_targets_values: List[tuple] = literal_eval(getenv("APP_TARGET_VALUES", default="[]"))

    image_confs = []
    for app_target, values_file_path in app_targets_values:
        single_image_conf = get_environment_config(app_target=app_target, values_file_path=values_file_path)
        if single_image_conf["AWS_ACCOUNT_ID"] is None:
            build_local_image(config=single_image_conf)
        else:
            build_ecr_image(config=single_image_conf)
        image_confs.append(single_image_conf)

    for single_image_conf in image_confs:
        update_image_into_file(config=single_image_conf)

    set_github_output("image_tag", GIT_REVISION)

if __name__ == "__main__":
    main()
