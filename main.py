import datetime
import json

from flask import Flask, request
import pandas as pd
import numpy as np
import sqlalchemy
from sqlalchemy import sql
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import requests
import logging
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.arima.model import ARIMA

# create console logger and file logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler1 = logging.StreamHandler()
handler1.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler1)
handler2 = logging.FileHandler('crypto-opportunity-service.txt')
handler2.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler2)

app = Flask(__name__, static_folder='crypto-opportunity-front-end/dist', static_url_path='')
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["300 per hour", "30 per minute"],
    storage_uri="memory://",
)
CORS(app)

secret_sauce = json.load(open('secret_sauce.json', ))


@app.route('/')
def status():
    return "ok"


@app.route("/daily-price-hist", methods=['GET'])
def daily_price_hist():
    coin = request.args.get('coin')
    logger.info(f"price-hist request for coin {coin}")
    data = fetch_daily_data(coin)
    return data.to_json(orient="records")


@app.route("/forecast-timeseries", methods=['GET'])
def forecast_timeseries():
    coin = request.args.get('coin')
    logger.info(f"forecast request for coin {coin}")
    data = fetch_daily_data(coin)
    predictions = predict(data)
    return predictions.to_json(orient='records')


@app.route("/forecast-results", methods=['GET'])
def forecast_results():
    coin = request.args.get('coin')
    logger.info(f"forecast request for coin {coin}")
    data = fetch_daily_data(coin)
    predictions = predict(data)
    last_close = predictions['close'].iloc[-8]
    last_close_day = predictions['date'].iloc[-8]
    next_day_price = predictions['close'].iloc[-7]
    seven_day_price = predictions['close'].iloc[-1]
    return pd.DataFrame(data={'last_close': [last_close],
                              'last_close_day': [last_close_day],
                              'next_day_price': [next_day_price],
                              'seven_day_price': [seven_day_price],
                              'coin': coin}).to_json(orient='records')


def fetch_daily_data(coin: str):
    data = fetch_data_from_db(coin)
    if not is_db_up_to_date(data):
        logger.info("db not up to date")
        new_data = fetch_daily_data_from_coinbase(coin)
        add_new_data_to_db(new_data, data)
    else:
        logger.info("db up to date")
    return data


def add_new_data_to_db(new_data: pd.DataFrame, data: pd.DataFrame):
    if data is None or data.empty:
        to_add = new_data
    else:
        to_add = new_data[new_data['date'] > data['date'].max().tz_localize(None)]
    if to_add.empty:
        logger.warning("no new data to add despite calling coinbase for it")
    else:
        logger.info(f"adding {len(to_add)} new rows to db")
        conn = get_connection()
        to_add.to_sql('crypto_prices', conn, if_exists='append', index=False)
        conn.commit()


def fetch_daily_data_from_coinbase(coin):
    logger.info(f"fetching daily data for {coin} from coinbase")
    symbol = coin + '-USD'
    url = f'https://api.pro.coinbase.com/products/{symbol}/candles?granularity=86400'
    response = requests.get(url)
    if response.status_code == 200:  # check to make sure the response from server is good
        data = pd.DataFrame(json.loads(response.text), columns=['unix', 'low', 'high', 'open', 'close', 'volume'])
        data['date'] = pd.to_datetime(data['unix'], unit='s')  # convert to a readable date
        data.drop('unix', axis=1, inplace=True)  # drop the unix column
        data['vol_fiat'] = data['volume'] * data['close']
        data['coin'] = coin
        return data
    logger.info(f"Got bad response from coinbase: {response.status_code}")
    return None  # hopefully we never get here


def fetch_data_from_db(coin: str):
    conn = get_connection()
    data = pd.read_sql(sql.text(f"select coin, open, high, low, close, date, vol_fiat, volume"
                                f" from crypto_prices where coin = '{coin}'"), conn)
    conn.commit()
    return data


def get_connection():
    return sqlalchemy.create_engine(secret_sauce['db_conn_string']).connect()


def is_db_up_to_date(data: pd.DataFrame):
    if data is None or data.empty:
        return False
    db_date = data['date'].max().tz_localize(None)
    now_gmt = pd.Timestamp.now(tz='GMT').tz_localize(None)
    yesterday = now_gmt - pd.Timedelta(days=1)
    return db_date > yesterday


def predict(hist_data: pd.DataFrame):
    close_data = hist_data[['date', 'close']]
    close_data = close_data.set_index('date')
    close_data_log = np.log(close_data)
    close_data_log.dropna(inplace=True)
    model = ARIMA(close_data_log, order=(2, 1, 2))
    results = model.fit()
    forecast = results.forecast(steps=7).to_frame()
    last_day = close_data_log.index.to_series().iloc[-1]
    forecast['date'] = [datetime.timedelta(days=i) + last_day for i in range(1, 8)]
    forecast = forecast.rename(columns={'predicted_mean': 'close'})
    data_plus_forecast = pd.concat([close_data_log.reset_index(None), forecast])
    data_plus_forecast['close'] = np.exp(data_plus_forecast['close'])
    return data_plus_forecast


if __name__ == '__main__':
    app.run(port=5000, debug=True)
