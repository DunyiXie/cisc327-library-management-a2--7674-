# Use a small official Python image
FROM python:3.11-slim

# Set workdir inside the container
WORKDIR /app

# Avoid writing .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system deps (optional, but helpful if you use SQLite / gcc, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency list and install Python packages
# Make sure requirements.txt is in your project root
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . /app

# Tell Flask which app to run
# ⚠️ If your entry file is not app.py, change this to e.g. "main.py" or "wsgi.py"
ENV FLASK_APP=app.py

# Flask must listen on all interfaces in the container
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Expose port 5000 from the container
EXPOSE 5000

# Run the Flask dev server
# The SQLite DB file will be created/used inside the container filesystem
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
