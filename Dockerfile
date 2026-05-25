FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    glpk-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app

COPY . .

CMD ["python", "-m", "app.main"]
