
FROM python:3.12-slim


RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /code


COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]