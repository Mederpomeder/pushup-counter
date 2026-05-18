# Use a lightweight official Python runtime base image
FROM python:3.12-slim

# Install system dependencies required for OpenCV and graphics handling
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /code

# Copy the requirements file into the container first to optimize caching
COPY ./requirements.txt /code/requirements.txt

# Install all the python packages listed in your requirements file
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy your local app folder code into the container working directory
COPY ./app /code/app

# Tell Docker to start your live FastAPI app using Uvicorn when the container launches
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]