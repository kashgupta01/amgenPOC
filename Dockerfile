FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python -c "from src.data_plane.database import initialize_database; initialize_database()"

EXPOSE 5000

CMD ["python", "-m", "flask", "--app", "src/integration_plane/app.py", "run", "--host=0.0.0.0", "--port=5000"]
