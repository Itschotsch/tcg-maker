# This Docker container is used to run the Python application.
# It is based on the official Python image and installs the required dependencies.
# The entrypoint is set to run the application.
# The application (in ./app) is not copied into the container, but mounted as a volume when the container is started.
# This way, the application can be updated without rebuilding the container.

# Use the official Python image
FROM python:3.11-slim

# Set the working directory
RUN mkdir /app
WORKDIR /app

# Expose the port
EXPOSE 8000

# Mount the application as a volume
VOLUME /app

# Install the required dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Initialize Playwright
RUN python -m playwright install
RUN python -m playwright install-deps

# Set the entrypoint to run the application
# Use the arguments: --web
# ENTRYPOINT ["python", "main.py"]
CMD ["python", "-u", "main.py", "--web"]