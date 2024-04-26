FROM python:3.12.3-slim-bullseye

COPY . /app/
WORKDIR /app

RUN pip install -r requirements.txt 
RUN rm -f .env .env.ci .env.default

CMD ["uvicorn", "--reload", "main:app"]