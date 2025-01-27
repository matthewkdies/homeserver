#!/bin/sh
pg_isready -q -d mealie -U "$(cat /run/secrets/POSTGRES_USER)"
