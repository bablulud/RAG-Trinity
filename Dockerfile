# Use a lightweight official Python image as the base
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
# We do this first to leverage Docker's build cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Set environment variables for API keys and other secrets
# IMPORTANT: Use environment variables, not hardcoded keys!
ENV OPENAI_API_KEY=your_default_key

# Command to run the application when the container starts
# This will run your main script with the appropriate arguments
CMD ["python", "main.py"]