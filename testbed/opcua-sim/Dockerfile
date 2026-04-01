FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server.py .
COPY server_all_entities.py .

EXPOSE 4840
CMD ["python", "server.py"]
