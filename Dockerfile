FROM python:3.6-alpine

RUN apk add --no-cache --virtual .build-deps gcc musl-dev \
    && pip install --no-cache-dir dumb-init \
    && apk del --no-cache .build-deps

COPY . /lpipe
RUN pip install --no-cache-dir /lpipe

ENTRYPOINT ["dumb-init", "--", "lpipe"]
