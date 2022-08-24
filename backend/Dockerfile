FROM python:3.8-slim

WORKDIR /backend

COPY requirements.txt /backend/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . /backend
ENV PYTHONUNBUFFERED=1
EXPOSE 5000
CMD ["python", "-u", "main.py"]