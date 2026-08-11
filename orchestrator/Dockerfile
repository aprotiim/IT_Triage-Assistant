FROM python:3.12-slim

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY it_triage_orchestrator ./it_triage_orchestrator

ENV PORT=8080
EXPOSE 8080

CMD ["python", "main.py"]
