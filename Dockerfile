FROM python:3.11-slim-bookworm

LABEL maintainer="fahmula"

RUN adduser pythonapp

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl iputils-ping gosu && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN chown -R pythonapp:pythonapp /app

ENV PYTHONUNBUFFERED=1

# Remove USER pythonapp line - entrypoint will handle user switching
# USER pythonapp

EXPOSE 5000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5000", "app:app"]