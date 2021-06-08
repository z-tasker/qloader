#!/bin/bash -e

REPO="ialcloud"
BROWSERS_BASE_VERSION=$(cat "./base-image/version")
VERSION=$(cat "./pyproject.toml" | sed -n 's/^version = "\(.*\)"$/\1 /gp' | xargs)

echo ""
echo "Building ${REPO}/browsers-base:${BROWSERS_BASE_VERSION}"
echo ""

cd ./base-image && \
docker build -t ${REPO}/browsers-base:${BROWSERS_BASE_VERSION} .

if [ "${1}" == "--push" ]; then
  docker push ${REPO}/browsers-base:${BROWSERS_BASE_VERSION}
fi


echo ""
echo "Building ${REPO}/qloader:${VERSION}"
echo ""

poetry export --without-hashes -f requirements.txt > requirements.txt
poetry build
docker build --build-arg BROWSERS_BASE_VERSION=${BROWSERS_BASE_VERSION} --build-arg VERSION=${VERSION} -t ${REPO}/qloader:"${VERSION}" .


if [ "${1}" == "--push" ]; then
  docker push ${REPO}/qloader:"${VERSION}"
fi
