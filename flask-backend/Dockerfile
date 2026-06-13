FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn
RUN apt-get update && apt-get install -y libimage-exiftool-perl ffmpeg
# Copy project files
COPY . .

# Expose the port (we'll use 8001 to avoid clashing with your other site)
EXPOSE 8002

# Run Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8001", "run:app", "--timeout", "600", "--access-logfile", "-", "--error-logfile", "-"]
