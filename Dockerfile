# Use an official Python runtime as a parent image
FROM python:3.11.5-slim

# Define environment variable
ENV DJANGO_SETTINGS_MODULE=djisco.settings.prod

# Set environment variables:
# Python won't try to write .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
# Python won't buffer stdout and stderr
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the current directory contents into the container at /app/
COPY . /app/

# Collect static files
RUN python manage.py collectstatic --no-input

# Make port 8050 available to the world outside this container
EXPOSE 8050


# Run gunicorn when the container launches
CMD ["gunicorn", "djisco.wsgi:application", "--bind", "0.0.0.0:8050"]