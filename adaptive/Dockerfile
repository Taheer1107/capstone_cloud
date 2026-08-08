FROM python:3.11-slim

WORKDIR /app

COPY adaptive/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY adaptive /app/adaptive
WORKDIR /app/adaptive

ENV PORT=5000
EXPOSE 5000

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 1 --timeout 120 backend:app"]