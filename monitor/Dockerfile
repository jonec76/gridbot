FROM python:3.8-slim

WORKDIR /monitor

COPY requirements.txt /monitor/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . /monitor
ENV PYTHONUNBUFFERED=1
CMD ["python", "-u", "monitor.py"]