# Use Python 3.11 as specified in the PRD
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code into the container at /app
COPY src/ /app/

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV NAME panosMCP

# Run main.py when the container launches
CMD ["python", "main.py"]
