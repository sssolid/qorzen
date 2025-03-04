# Use an official Python image as a base
FROM python:3.12

# Set the working directory
WORKDIR /app

# Copy Qorzen source code into the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose necessary ports (if applicable)
EXPOSE 8000

# Set the command to run the app
CMD ["python", "-m", "qorzen"]
