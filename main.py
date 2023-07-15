import json

from flask import Flask, request
import pandas as pd
import sqlalchemy
from sqlalchemy import sql
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import requests
import logging


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

secret_sauce = json.load(open('secret_sauce.json',))


@app.route('/')
def status():
    return "ok"


@app.route("/daily-price-hist", methods=['GET'])
def daily_price_hist():
    coin = request.args.get('coin')
    logger.info(f"price-hist request for coin {coin}")
    data = fetch_daily_data(coin)
    return data.to_json(orient="records")


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
    return None # hopefully we never get here


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


if __name__ == '__main__':
    app.run(port=5000, debug=True)
