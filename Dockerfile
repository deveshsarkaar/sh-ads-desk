FROM python:3.12-slim

WORKDIR /app
COPY . /app

ENV HOST=0.0.0.0 \
    PORT=8000 \
    SH_ADS_DATA_DIR=/app/data \
    PYTHONUNBUFFERED=1

VOLUME ["/app/data"]
EXPOSE 8000

# No pip install needed: standard library only.
CMD ["python", "run.py"]
