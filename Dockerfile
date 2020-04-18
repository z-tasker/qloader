FROM debian:bullseye

# browsers to run the tests
RUN echo "deb http://deb.debian.org/debian/ unstable main contrib non-free" >> /etc/apt/sources.list && \ 
    apt update && \
    apt install -y firefox

RUN apt install -y wget unzip
 
RUN wget -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
  apt install -y /tmp/chrome.deb

# Gecko Driver
ENV GECKODRIVER_VERSION 0.26.0
RUN wget --no-verbose -O /tmp/geckodriver.tar.gz https://github.com/mozilla/geckodriver/releases/download/v$GECKODRIVER_VERSION/geckodriver-v$GECKODRIVER_VERSION-linux64.tar.gz && \
  rm -rf /opt/geckodriver && \
  tar -C /opt -zxf /tmp/geckodriver.tar.gz && \
  rm /tmp/geckodriver.tar.gz && \
  mv /opt/geckodriver /opt/geckodriver-$GECKODRIVER_VERSION && \
  chmod 755 /opt/geckodriver-$GECKODRIVER_VERSION && \
  ln -fs /opt/geckodriver-$GECKODRIVER_VERSION /usr/bin/geckodriver && \
  ln -fs /opt/geckodriver-$GECKODRIVER_VERSION /usr/bin/wires

# Chrome Driver
ENV CHROMEDRIVER_VERSION 2.41
RUN wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/2.41/chromedriver_linux64.zip && \
  unzip /tmp/chromedriver.zip -d /tmp/ && \
  mv /tmp/chromedriver /usr/local/bin

RUN apt install -y python3.8 python3-pip

RUN mkdir /qload 
ADD requirements.txt /qload/
RUN pip3 install -r /qload/requirements.txt

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONUNBUFFERED=1

RUN firefox --version
RUN pip3 list selenium
RUN geckodriver --version
RUN chromedriver --version
ADD browserdriver.py query.py /qload/
ENTRYPOINT ["/qload/query.py"]
