# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.1] - 2025/11/17
### Fixed
- To resolve a compatibility issue with the Docker API version, the image used for Watchtower was changed to a fork of the original project.

## [0.9.0] - 2025/11/06
### Changed
- Migrated the Pi-hole instances within my network from v5 to v6 according to their [migration docs](https://docs.pi-hole.net/docker/upgrading/), which are excellent ([#19](https://github.com/matthewkdies/homeserver/issues/37))!

## [0.8.0] - 2025/10/22
### Added
- A script that contains global logging functions.
- A script that handles automatic system backups ([#37](https://github.com/matthewkdies/homeserver/issues/37))

### Changed
- Upgraded Authelia to 4.39.11.
- The existing script to backup volumes was modified to use different directories, a different logfile, and use the "global" functions.

## [0.7.0] - 2025/08/19
### Added
- A [Maintainerr](https://docs.maintainerr.info/latest/) container used for creating rules that create collections within Plex marking content for deletion, eventually deleting them.


## [0.6.0] - 2025/06/04
### Added
- A [Meloday](https://github.com/trackstacker/meloday) container used for automatically creating playlists for a Plex music library ([#35](https://github.com/matthewkdies/homeserver/issues/35)).


## [0.5.0] - 2025/05/24
### Added
- A [kcal](https://github.com/kcal-app/kcal) container used for nutrition tracking ([#33](https://github.com/matthewkdies/homeserver/issues/33)).
  > This configuration is more complicated than typical self-hosted web-apps. I've configured it to run with a non-standard UID + GID (using `su-exec` and a custom script for setting environment variables based on Docker secrets files) for security reasons. It also contains many more containers than a typical self-hosted web app.

## [0.4.0] - 2025/04/06
### Added
- A second [Radarr](https://radarr.video/) container used for getting certain fair-use movies in 4K, alongside the existing 1080p fair-use movie ([#31](https://github.com/matthewkdies/homeserver/issues/31)).
- A `backup_volumes.sh` script that does the following:
  - Confirms availability of network mount intended for backups.
  - Prunes unused Docker volumes.
  - Backs up all Docker volumes by using a transient container with volume mounts create a tarfile of the data.
  - Cleans old backups by using timestamps to always keep 3 copies of each volume's backup tarfile and deleting any older than that.
  - Logs output to stdout and to a logfile for later access.
  > This script has been set to run daily with `crontab`.
- A `soulseek_config` volume to the `soulseek` service. I don't do anything with it, but the image contains a `VOLUME` instruction, so it was making an unnamed volume. This addition at least names the volume.

### Changed
- Updated Authelia to [4.39.1](https://github.com/authelia/authelia/releases/tag/v4.39.1).
  > This may be a fairly significant update for some users. It's not in my case, but just in case, here are the [user-friendly release notes](https://www.authelia.com/blog/4.39-release-notes/).


## [0.3.0] - 2025/03/26
### Added
- Mealie now has OpenAI integration, which will allow users to import recipes from images and to use the OpenAI ingredient parser.
- The `chore` tag is now applied to issues created with the chore issue template.
- Sensible `depends_on` settings to the Arr-suite's compose file, so that apps no longer behave strangely on startup if they start before another app is running.
- [LubeLogger](https://github.com/hargata/lubelog) has been added for tracking vehicle maintenance and mileage ([#17](https://github.com/matthewkdies/homeserver/issues/17)).
- slskd + soularr ([#25](https://github.com/matthewkdies/homeserver/issues/25)):
  - [slskd](https://github.com/slskd/slskd?tab=readme-ov-file#slskd) has been added for using the Soulseek network to connect to other users for sending and receiving music in the public domain.
  - [soularr](https://github.com/mrusse/soularr?tab=readme-ov-file#about) has been added for connecting Lidarr to slskd.

### Changed
- Mealie has been updated to 2.8.0.
- The `BASE_URL` environment variable in Mealie is now set directly rather than with a secret.
- The remaining secrets in Mealie are now set with their `<env_varname>_FILE` variable counterpart as an environment variable.
- The script I use to update and push my edits to the football pool website now uses a full path so I can call it from anywhere.
- Applying Shellcheck edits to scripts.
- All Docker Compose files now use a consistent environment variable definition of `KEY: value` (rather than `- KEY=value`) ([#6](https://github.com/matthewkdies/homeserver/issues/6)).
- The script I use to update Caddy now uses `docker compose up --detach` rather than `docker compose restart`.

### Fixed
- An error within my Caddy setup in which ACME DNS Challenges would fail due to my local DNS (Pi-hole) being used. Adding the Caddy `tls -> resolvers` directive directed to a public DNS resolves the issue.

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
