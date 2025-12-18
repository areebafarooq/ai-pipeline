FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy app files
COPY app/ ./

# Install dependencies (if using Flask)
RUN pip install --no-cache-dir flask

# Expose port
EXPOSE 8000

# Run the app
CMD ["python", "app.py"]