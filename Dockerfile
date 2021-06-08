ARG VERSION
ARG BROWSERS_BASE_VERSION
FROM ialcloud/browsers-base:$BROWSERS_BASE_VERSION
ARG VERSION

ADD requirements.txt /home/admin/
RUN pip3 install -r /home/admin/requirements.txt

RUN mkdir ./dist
ADD dist/qloader-${VERSION}-py3-none-any.whl ./dist/

RUN pip3 install ./dist/qloader-${VERSION}-py3-none-any.whl

ADD bin/google-images-search.py ./

ENTRYPOINT ["python3", "./google-images-search.py"]
