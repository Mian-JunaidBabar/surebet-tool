# Use the latest official Python 3.12 on a slim Debian base
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Install curl for healthcheck and sqlite3 for debugging the DB
RUN apt-get update \
    # Install runtime utilities (curl, sqlite3) plus build deps so binary modules
    # like greenlet can be built if a compatible wheel isn't available on PyPI.
    && apt-get install -y \
    curl \
    sqlite3 \
    build-essential \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file
COPY requirements.txt .

# Upgrade pip/setuptools/wheel first (improves resolver and wheel handling),
# then install Python dependencies. Using --no-cache-dir reduces image size.
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create the data directory for the SQLite database
RUN mkdir -p /app/data

# Expose the port FastAPI/uvicorn will run on
EXPOSE 8000

# The command to start the FastAPI server
# --host 0.0.0.0 makes it accessible from outside the container
CMD ["uvicorn", "main:socket_app", "--host", "0.0.0.0", "--port", "8000"]