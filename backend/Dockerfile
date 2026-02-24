FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Railway sets PORT dynamically; default to 8000
ENV PORT=8000

EXPOSE ${PORT}

CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
