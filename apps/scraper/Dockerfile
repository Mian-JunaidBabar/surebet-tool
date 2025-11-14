# Use the official Microsoft Playwright image with Python
# This includes all necessary browsers and system dependencies
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install any additional Python dependencies we need
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# The default command to run when the container starts
# Run the FastAPI server using uvicorn
CMD ["uvicorn", "scraper:app", "--host", "0.0.0.0", "--port", "8001"]