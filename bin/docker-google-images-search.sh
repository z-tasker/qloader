#!/bin/bash -e

VERSION=$(cat "./pyproject.toml" | sed -n 's/^version = "\(.*\)"$/\1 /gp' | xargs)

docker run ialcloud/qloader:${VERSION} ${@}
