FROM python:3.10-alpine

WORKDIR /app

RUN apk update 

RUN apk add --update build-base ca-certificates python3 python3-dev ffmpeg

## ImageMagicK Installation ##
RUN apk add --no-cache imagemagick && \
apk add --no-cache imagemagick-dev 

RUN pip install --upgrade pip


# venv
ENV VIRTUAL_ENV=/home/app/venv

# python setup
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN export FLASK_APP=app.py

# Install pip packages
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY app.py /app

COPY *.json /app

EXPOSE 5000

CMD ["python", "app.py"]