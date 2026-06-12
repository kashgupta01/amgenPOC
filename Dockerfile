FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt uvicorn

COPY . .

ENV APP_ENV=prod

EXPOSE 8000

CMD ["uvicorn", "src.integration_plane.app:app", "--host", "0.0.0.0", "--port", "8000"]
