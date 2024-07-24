# crypto-opportunity-service

## Description

A service intended to predict the next day price of cryptocurrencies based on historical data.
It scrapes daily price data from coinbase to use in its predictions.
It uses an ARIMA model to make predictions about the price of a cryptocurrency the next day and next week.

## Setup

1. Assumes you have a database with the tables form the `schema` directory.
2. Assumes you have a .env file in the root project directory with the following variables:
    - `DATABASE_CONN_STRING`
3. Execute the `start.sh` script to start the app as a docker container.


## Development

Install dependencies: `pipenv install --dev`

run app: `pipenv run flask --app main:app run`

regen requirements.txt after adding a dependency: `pipenv lock -r > requirements.txt`

regenerate frontend assets (from `/crypto-opportunity-front-end`): `npm i && npm run build`
