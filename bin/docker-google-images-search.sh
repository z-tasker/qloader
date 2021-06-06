#!/bin/bash -e

OUTPUT_PATH="/tmp/qloader"
VERSION=$(cat "./pyproject.toml" | sed -n 's/^version = "\(.*\)"$/\1 /gp' | xargs)

mkdir -p ${OUTPUT_PATH}

docker run -v ${OUTPUT_PATH}:${OUTPUT_PATH} ialcloud/qloader:${VERSION} --output-path ${OUTPUT_PATH} ${@}
