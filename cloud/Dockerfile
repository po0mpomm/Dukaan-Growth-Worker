FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn pydantic httpx psycopg2-binary

COPY cloud/ /app/cloud/

EXPOSE 8001

CMD ["uvicorn", "cloud.app.main:app", "--host", "0.0.0.0", "--port", "8001"]
