FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app:/app/freeburg/vendor
WORKDIR /app
COPY freeburg/requirements-data.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt lxml html5lib numpy
COPY freeburg /app/freeburg
RUN useradd -r -m appuser && mkdir -p /data && chown appuser:appuser /data
USER appuser
ENTRYPOINT ["python", "-m"]
CMD ["freeburg.deploy.portable_scheduler"]
