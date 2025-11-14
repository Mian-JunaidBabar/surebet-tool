# Use the latest official Python 3.12 on a slim Debian base
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create the data directory for the SQLite database
RUN mkdir -p /app/data

# Expose the port FastAPI/uvicorn will run on
EXPOSE 8000

# The command to start the FastAPI server
# --host 0.0.0.0 makes it accessible from outside the container
CMD ["uvicorn", "main:socket_app", "--host", "0.0.0.0", "--port", "8000"]