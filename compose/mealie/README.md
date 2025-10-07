I clone and build my own version of Mealie because there's a bug that requires a local build ([see here for more info](https://github.com/mealie-recipes/mealie/issues/4563)).
I've cloned it like so:

```bash
cd ${COMPOSE_DIR}/mealie
git clone <mealie_clone_url>
mv mealie mealie_source
```

When new releases are published, I upgrade by pulling and then switching to the relevant tag:

```bash
cd ${COMPOSE_DIR}/mealie/mealie_source

# switch to the branch, since I detach the head below
git switch mealie-next

# stash my changes, then get the updates from upstream
git stash -m "Stashing my local changes of mealie."
git pull

# detach the HEAD to the desired release and re-apply my changes
git switch tags/<tag_name> --detach
git stash pop

# resolve any conflicts here, if needed
```

As you can tell, I choose to intentionally detach HEAD at the commit.
This is because I don't often make changes, only when upgrading the version.
You may choose not to do this if you'd like to make changes more often.
