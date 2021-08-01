FROM python:3.9-alpine

RUN --mount=type=bind,target=/app pip install -r /app/requirements.txt
COPY portainerhack /usr/local/lib/python3.9/site-packages/portainerhack

ENTRYPOINT [ "python", "-m", "portainerhack" ]
