# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## Unreleased
### Added
- The `chore` tag is now applied to issues created with the chore issue template.

### Changed
- The `BASE_URL` environment variable in Mealie is now set directly rather than with a secret.
- The remaining secrets in Mealie are now set with their `<env_varname>_FILE` variable counterpart as an environment variable.

### Removed
- The custom entrypoint script from the Mealie container.



## [0.2.0] - 2024/02/09
### Added
- Compose file for my Minecraft server.
- Compose file and custom configuration files for my local Pi-hole DNS'.
  - Route all local traffic over IPv4 only.
  - Create local SRV record for Minecraft server.
- A script for correcting the permissions and ownership recursively of the media directories, intended to be run as a crontab job.
- `README.md` files to the compose and scripts directories.

### Changed
- Added the `minecraft` subdomain to the dynamic DNS in Caddy, as I manually maintain a SRV record for Minecraft.
- Watchtower was set to ignore the football pool container in favor of manual management, since I create it myself.
- Watchtower was set to ignore Mealie while I wait on [a bug](https://github.com/mealie-recipes/mealie/issues/4563) to be fixed.
- The GitHub workflow now succeeds even if a release for the current version already exists, but skips making a new release.

### Removed
- The `compose/football-pool/Dockerfile`, as I build the image elsewhere.
- The `~/.docker/config.json` volume mount from Watchtower, as no private registries are needed.


## [0.1.0] - 2025/01/26
### Added
- Adding the Docker Compose files, other configuration files, and healthcheck scripts that stand up my home server.
  - Adding working documentation about some of the more complicated containers and my setup.
- Adding the scripts I use during normal PC usage. This includes scripts added to containers and those used as helper scripts.
- Set up the Git repository with a `README.md`, `LICENSE`, `.pre-commit-config.yaml`, `.gitignore`, and GitHub workflow file.
