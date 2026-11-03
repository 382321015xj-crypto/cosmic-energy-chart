FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 HOST=0.0.0.0
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements-v6.txt
EXPOSE 8000
CMD ["python", "run_server.py"]
