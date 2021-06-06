REPO="ialcloud"
VERSION=$(cat "./pyproject.toml" | sed -n 's/^version = "\(.*\)"$/\1 /gp' | xargs)

echo ""
echo "Building ${REPO}/qloader:${VERSION}"
echo ""

poetry export --without-hashes -f requirements.txt > requirements.txt
poetry build
docker build --build-arg VERSION=${VERSION} -t ialcloud/qloader:"${VERSION}" .


if [ "${1}" == "--push" ]; then
  docker push ialcloud/qloader:"${VERSION}"
fi
