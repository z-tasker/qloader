## qloader

qloader runs a query and tags results with metadata.


## running this program

download non-python dependencies:

to use Firefox you must have `geckodriver` installed
to use Chrome you must have `chromedriver` installed

`geckodriver` on debian:
```
wget -O /tmp/geckodriver.tar.gz https://github.com/mozilla/geckodriver/releases/download/v0.26.0/geckodriver-v0.26.0-linux64.tar.gz
tar -xvzf /tmp/geckodriver.tar.gz
mv /tmp/geckodriver /usr/local/bin/
```

`chromedriver` on debian:
```
wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/2.41/chromedriver_linux64.zip
unzip /tmp/chromedriver.zip
mv /tmp/chromedriver /usr/local/bin/
```

You can tell `query.py` which browser to use by setting the environment variable `QLOADER_BROWSER` to "Chrome" or "Firefox":

```
export QLOADER_BROWSER=Firefox
```

You must also have the browser in question installed.

### running with python:

Using [poetry](https://python-poetry.org/docs/) for python package management:

```
poetry install
mkdir -p /tmp/qloader
```

```
poetry run ./query.py \
  --experiment-name "null-test" \
  --hostname "null-tester" \
  --endpoint "google-images" \
  --metadata-path /tmp/qloader/metadata.json \
  --output-path "./downloads" \
  --skip-upload \
  --query-terms "Beautiful Complexity"

```

### docker

To facilitate running `qloader` on arbitrary systems, it is packaged into a public docker image `mgraskertheband/qloader`. To build and run this image locally (`docker` must be installed):

```
./build.sh 2.1.0
docker run \
    --shm-size=2g \
    -v /tmp/qloader:/tmp/qloader \
    mgraskertheband/qloader:2.1.0 \
        --experiment-name "null-test" \
        --hostname "null-tester" \
        --endpoint "google-images" \
        --metadata-path "/tmp/qloader/metadata.json" \
        --output-path "/tmp/qloader" \
        --skip-upload \
        --query-terms "Beautiful Complexity"
```

Switch browsers by setting `--env QLOADER_BROWSER=Chrome` in the `docker run` command, before the image name.

This command mounts /tmp/qloader into the docker container, so that results gathered in docker are available to the host. This mount is also used to provide `metadata.json` to the query runner.
