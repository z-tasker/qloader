if [ -z "${1}" ]; then
  echo "provide docker tag"
  exit 1
fi

poetry export -f requirements.txt > requirements.txt
docker build -t mgraskertheband/qloader:"${1}" .
