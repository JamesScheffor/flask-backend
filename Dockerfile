# Use an official Python runtime as a base image
FROM python:3.8-slim

# Install system dependencies required for pdf2image
RUN apt-get update && \
    apt-get install -y poppler-utils

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable for OpenAI API key
ENV OPENAI_API_KEY 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


# Run app.py when the container launches
CMD ["python", "app.py"]
