FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /code

# PyMySQL là driver Python thuần, không cần ODBC/native database driver.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /code/app
COPY ./scripts /code/scripts
COPY ./tests /code/tests
COPY ./sql /code/sql

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
