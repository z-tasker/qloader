if [ -z "${1}" ]; then
  echo "provide docker tag"
  exit 1
fi

docker build -t mgraskertheband/qloader:"${1}" .
