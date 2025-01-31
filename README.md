# Home Server

![Version](https://img.shields.io/github/v/release/matthewkdies/homeserver)
![License](https://img.shields.io/github/license/matthewkdies/homeserver)
![Issues](https://img.shields.io/github/issues/matthewkdies/homeserver)
![Pull Requests](https://img.shields.io/github/issues-pr/matthewkdies/homeserver)
![Docker Compose Version](https://img.shields.io/badge/Docker%20Compose-v2-blue)
![Secrets Scan](https://img.shields.io/badge/Secrets%20Scan-Passing-brightgreen)

# Installation

Clone the repository to wherever you'd like on your host machine.
Pre-requisuites for this repository are essentially just Docker, though I might be forgetting something.
The scripts themselves are intended to run in `sh` or `bash`.
A lot of this is tightly coupled with my desired and existing setup, though I hope that things in here are helpful to you regardless!

```
# ssh
git clone git@github.com:matthewkdies/homeserver.git

# https
git clone https://github.com/matthewkdies/homeserver.git
```

# Prerequisites

Docker and Docker Compose must be available.

# Setup

I use a couple of environment variables throughout the stack that you might want to set for convenience.
To set them, I created a file at `~/.envvars` in which I export my environment variables, currently set with the following:
```bash
# configuration/docker dirs
export DOCUMENTS_DIR="/home/matthewkdies/Documents"
export DOCKER_DIR="${DOCUMENTS_DIR}/docker"
export COMPOSE_DIR="${DOCUMENTS_DIR}/compose"
export SCRIPTS_DIR="${DOCUMENTS_DIR}/scripts"
export SECRETS_DIR="${DOCKER_DIR}/secrets"
```

There are some other variables that I am not showing here, but that's the gist.
I then added to my `~/.bashrc` file to get them loaded:
```bash
# load environment variables
if [ -f ~/.envvars ]; then
    . ~/.envvars
fi
```

# Running

In order to run any of the files to start the included containers, I make the following assumptions:
1. You have a working knowledge of [Docker Compose](https://docs.docker.com/reference/compose-file/).
2. You will be able to interpret the files to see what you need to change to fit your specific setup. For example, changing the paths of secrets files or the values of environment variables.

Beyond that, starting a stack is as simple as `docker compose --file <path_to_file> up --detach`.

# Basic Structure

- [`compose/`](./compose/): Contains the Docker Compose files, Dockerfiles, configuration files, healthscripts, and documentation related to the Docker containers on my home server.
- [`scripts/`](./scripts/): Contains the scripts that I use within containers and in common use.
- [`changelog.md`](./changelog.md): Documentation on updates to the repository.
- [`.pre-commit-config.yaml`](./.pre-commit-config.yaml): A `pre-commit` config file that runs the [`detect-secrets`](https://github.com/Yelp/detect-secrets) CLI to prevent secrets from inadvertantly being committed to the remote repository.
- [`.github/workflows`](./.github/workflows/): Contains custom workflows, which currently includes making releases automatically.
