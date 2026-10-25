FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# dependencies first, so a code change does not reinstall them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .

EXPOSE 5000

# 0.0.0.0 so the 5000:5000 port mapping reaches the server - flask binds loopback by default
CMD ["flask", "--app", "app", "run", "--host=0.0.0.0", "--port=5000"]
