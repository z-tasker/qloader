ARG VERSION
FROM debian:bullseye
ARG VERSION

# browsers to run the tests
RUN echo "deb http://deb.debian.org/debian/ unstable main contrib non-free" >> /etc/apt/sources.list && \ 
    apt update && \
    apt install -y firefox

RUN apt-get install -y wget unzip gnupg

RUN wget -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
  apt install -y /tmp/chrome.deb

# Gecko Driver
ENV GECKODRIVER_VERSION 0.29.1
RUN wget --no-verbose -O /tmp/geckodriver.tar.gz https://github.com/mozilla/geckodriver/releases/download/v$GECKODRIVER_VERSION/geckodriver-v$GECKODRIVER_VERSION-linux64.tar.gz && \
  rm -rf /opt/geckodriver && \
  tar -C /opt -zxf /tmp/geckodriver.tar.gz && \
  rm /tmp/geckodriver.tar.gz && \
  mv /opt/geckodriver /usr/local/bin/geckodriver-$GECKODRIVER_VERSION && \
  chmod 755 /usr/local/bin/geckodriver-$GECKODRIVER_VERSION && \
  ln -fs /usr/local/bin/geckodriver-$GECKODRIVER_VERSION /usr/local/bin/geckodriver && \
  ln -fs /usr/local/bin/geckodriver-$GECKODRIVER_VERSION /usr/local/bin/wires

# Chrome Driver
ENV CHROMEDRIVER_VERSION 103.0.5060.134
RUN wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip && \
  unzip /tmp/chromedriver.zip -d /tmp/ && \
  mv /tmp/chromedriver /usr/local/bin

RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -

WORKDIR /tmp
ENV PYTHON_VERSION 3.8.10
RUN apt -y update && \
  apt -y install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libsqlite3-dev libreadline-dev libffi-dev curl libbz2-dev && \
  curl -O https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tar.xz && \
  tar -xf Python-$PYTHON_VERSION.tar.xz && \
  cd Python-$PYTHON_VERSION && \
  ./configure --enable-optimizations && \
  make -j 4 && \
  make altinstall

RUN apt-get -y update && \ 
  apt-get install -y python3-pip --fix-missing

RUN mkdir -p /etc/sudoers.d && \  
  addgroup --gid 1000 admin && \
  adduser --disabled-password --gecos "" --uid 1000 --gid 1000 admin && \
  echo "admin ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/admin && chmod 400 /etc/sudoers.d/admin

USER admin

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONUNBUFFERED=1

RUN firefox --version
RUN pip3 list selenium
RUN geckodriver --version
RUN chromedriver --version

WORKDIR /home/admin/
