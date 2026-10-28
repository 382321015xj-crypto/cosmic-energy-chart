FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 HOST=0.0.0.0
WORKDIR /app
COPY . /app
EXPOSE 8000
CMD ["python", "run_server.py"]
