I clone and build my own version of Mealie because there's a bug that requires a local build ([see here for more info](https://github.com/mealie-recipes/mealie/issues/4563)).
I've cloned it like so:

```bash
cd ${COMPOSE_DIR}/mealie
git clone <mealie_clone_url>
mv mealie mealie_source
```

When new releases are published, I upgrade by pulling and then switching to the relevant tag using the below set of commands.
In order to ensure I stay up-to-date, I have release notifications enabled for the GitHub repository.
You can do this as well if you'd like by signing in to GitHub, navigating to the Mealie repository, and selecting `Watch`.
From here, click `Custom` and check the `Releases` box and then hit apply.
You will now receive emails at the email associated with your GitHub account when Mealie publishes a new release.

```bash
cd ${COMPOSE_DIR}/mealie/mealie_source

# stash my changes
git stash -m "Stashing my local changes of mealie."

# switch to the branch, since I detach the head below
git switch mealie-next
git pull  # get updates from upstream

# detach the HEAD to the desired release and re-apply my changes
git switch tags/<tag_name> --detach
git stash pop

# resolve any conflicts here, if needed
```

As you can tell, I choose to intentionally detach HEAD at the commit.
This is because I don't often make changes, only when upgrading the version.
You may choose not to do this if you'd like to make changes more often.

Following these commands, I also update the version that I tag the image with in the [compose file](mealie-compose.yaml).
Then I rebuild with `docker compose -f <path_to_compose_file> build` and deploy with `docker compose -f <path_to_compose_file> up -d`.
