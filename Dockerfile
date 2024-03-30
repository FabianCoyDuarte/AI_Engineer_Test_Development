FROM python:3.10.4-alpine3.15

ENV PYTHONUNBUFFERED=1
ENV PATH="/scripts:${PATH}"
# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Collect static files (if needed)
WORKDIR /app/app
RUN python manage.py collectstatic --noinput

# Run Gunicorn with your Django application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app.wsgi:application"]


