import datetime
import json
import sys
from cachetools import cached, LRUCache
from threading import Thread

from flask import Flask, request, redirect
import pandas as pd
import numpy as np
from sqlalchemy import sql
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import requests
import logging
from statsmodels.tsa.arima.model import ARIMA
import time
from dotenv import load_dotenv, find_dotenv
from repos.db_utils import get_connection
from repos.crypto_predictions_arima import CryptoPredictionsArimaRepository


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

RH_COINS = ['BTC', 'ETH', 'ADA', 'SOL', 'DOGE', 'SHIB', 'AVAX', 'ETC', 'UNI', 'LTC', 'LINK', 'XLM', 'AAVE', 'XTZ',
            'BCH']
_ = load_dotenv(find_dotenv())

# define repos
crypto_predictions_arima_repo = CryptoPredictionsArimaRepository()


@app.route('/')
def hello():
    return redirect("/index.html", code=302)


@app.route("/daily-price-hist", methods=['GET'])
def daily_price_hist():
    coin = request.args.get('coin')
    request.args.get('coin')
    logger.info(f"price-hist request for coin {coin}")
    data = fetch_up_to_date_daily_data(coin)
    return data.to_json(orient="records")


@app.route("/forecast-timeseries", methods=['GET'])
def forecast_timeseries():
    coin = request.args.get('coin')
    p = int(request.args.get('p')) if request.args.get('p') else 2
    d = int(request.args.get('d')) if request.args.get('d') else 1
    q = int(request.args.get('q')) if request.args.get('q') else 2
    logger.info(f"forecast request for coin {coin}")
    data = fetch_up_to_date_daily_data(coin)
    predictions = predict_next_7(data, p, d, q)
    return predictions.to_json(orient='records')


@app.route("/forecast-results", methods=['GET'])
def forecast_results():
    coin = request.args.get('coin')
    p = int(request.args.get('p')) if request.args.get('p') else 2
    d = int(request.args.get('d')) if request.args.get('d') else 1
    q = int(request.args.get('q')) if request.args.get('q') else 2
    logger.info(f"forecast request for coin {coin}")
    data = fetch_up_to_date_daily_data(coin)
    predictions = predict_next_7(data, p, d, q)
    last_close = predictions['close'].iloc[-8]
    last_timestamp_reported = predictions['date'].iloc[-8]
    next_day_price = predictions['close'].iloc[-7]
    seven_day_price = predictions['close'].iloc[-1]
    save_predictions_for_coin(last_close, next_day_price, seven_day_price, coin, last_timestamp_reported, p, d, q)
    return pd.DataFrame(data={'last_close': [last_close],
                              'last_timestamp_reported': [last_timestamp_reported],
                              'next_day_price': [next_day_price],
                              'seven_day_price': [seven_day_price],
                              'coin': coin}).to_json(orient='records')


@app.route("/forecast-results-async", methods=['GET'])
def initiate_async():
    thread = Thread(target=forecast_results_async)
    thread.start()
    return {"success": True}


def forecast_results_async():
    for coin in RH_COINS:
        for p, d, q in ((2, 1, 2), (3, 4, 3), (3, 2, 3)):
            logger.info(f"forecast request for coin {coin} with p={p}, d={d}, q={q}")
            data = fetch_up_to_date_daily_data(coin)
            predictions = predict_next_7(data, p, d, q)
            last_close = predictions['close'].iloc[-8]
            last_timestamp_reported = predictions['date'].iloc[-8]
            next_day_price = predictions['close'].iloc[-7]
            seven_day_price = predictions['close'].iloc[-1]
            save_predictions_for_coin(last_close, next_day_price, seven_day_price, coin, last_timestamp_reported, p, d, q)
        time.sleep(10)


@app.route("/forecast-results-all", methods=['GET'])
def forecast_results_all():
    conn = get_connection()
    results = crypto_predictions_arima_repo.get_data_for_last_day()
    conn.commit()
    conn.close()
    results['next_day_pct_change'] = (results['next_day_price'] - results['last_close']) * 100 / results['last_close']
    results['seven_day_pct_change'] = (results['seven_day_price'] - results['last_close']) * 100 / results['last_close']
    results['id'] = range(len(results))
    return results.to_json(orient='records')


@app.route("/coin-model-performance", methods=['GET'])
def coin_model_performance():
    coin = request.args.get('coin')
    p = int(request.args.get('p')) if request.args.get('p') else 2
    d = int(request.args.get('d')) if request.args.get('d') else 1
    q = int(request.args.get('q')) if request.args.get('q') else 2
    perf = calculate_historical_coin_performance(coin, p, d, q)
    perf['id'] = range(len(perf))
    return perf.to_json(orient='records')


@app.route("/composite-model-performance", methods=['GET'])
def composite_model_performance():
    p = int(request.args.get('p')) if request.args.get('p') else 2
    d = int(request.args.get('d')) if request.args.get('d') else 1
    q = int(request.args.get('q')) if request.args.get('q') else 2
    return composite_strategy_performance(p, d, q).to_json(orient='records')


@app.route("/all-model-performance", methods=['GET'])
def all_model_performance():
    df = composite_strategy_performance(2, 1, 2)
    df = pd.concat([df, composite_strategy_performance(3, 4, 3)])
    df = pd.concat([df, composite_strategy_performance(3, 2, 3)])
    for coin in RH_COINS:
        logger.info(f"calculate_historical_coin_performance({coin}, 2, 1, 2)")
        df = pd.concat([df, calculate_historical_coin_performance(coin, 2, 1, 2)])
        df = pd.concat([df, calculate_historical_coin_performance(coin, 3, 4, 3)])
        df = pd.concat([df, calculate_historical_coin_performance(coin, 3, 2, 3)])
    df['total_performance_vs_coin'] = df['total_performance'] - df['hold_performance']
    df['id'] = range(len(df))
    return df.to_json(orient='records')


@cached(cache=LRUCache(maxsize=None))
def calculate_historical_coin_performance(coin, p, d, q):
    logger.info(f"fetching arima prediction data {coin}")
    forecasts = crypto_predictions_arima_repo.get_coin_forecasts_with_actual(coin, p, d, q)
    logger.info(f"calculating period performances for {coin}")
    total_performance = calc_period_change(forecasts, None)
    last_month_performance = calc_period_change(forecasts, 30)
    last_week_performance = calc_period_change(forecasts, 7)
    last_day_performance = calc_period_change(forecasts, 1)
    hold_performance = (forecasts['last_close'].iloc[-1] / forecasts['last_close'].iloc[0]) * 100 - 100 if len(
        forecasts) > 0 else 0
    return pd.DataFrame(data={'total_performance': [total_performance],
                              'last_timestamp_reported': [
                                  forecasts['last_timestamp_reported'].max() + pd.Timedelta(days=1)],
                              'last_month_performance': [last_month_performance],
                              'last_week_performance': [last_week_performance],
                              'last_day_performance': [last_day_performance],
                              'hold_performance': [hold_performance],
                              'total_days': [len(forecasts)],
                              'coin': coin,
                              'p': p,
                              'd': d,
                              'q': q})


def composite_strategy_performance(p, d, q):
    forecasts = None
    logger.info(f"getting all coin perf for composite_strategy_performance({p}, {d}, {q})")
    for coin in RH_COINS:
        logger.info(f"get_coin_forecasts_with_actual({coin}...) - caching enabled - fetch from DB")
        if forecasts is None:
            forecasts = crypto_predictions_arima_repo.get_coin_forecasts_with_actual(coin, p, d, q)
        else:
            forecasts = pd.concat([forecasts, crypto_predictions_arima_repo.get_coin_forecasts_with_actual(coin, p, d, q)])
    logger.info(f"running performance calculations")
    forecasts['next_day_pct_change_expected'] = (forecasts['next_day_price'] - forecasts['last_close']) * 100 / forecasts['last_close']
    forecasts['next_day_pct_change_actual'] = (forecasts['next_day_actual'] - forecasts['last_close']) * 100 / forecasts['last_close']
    idx = forecasts.groupby(['last_timestamp_reported'])['next_day_pct_change_expected'].transform(max) == forecasts['next_day_pct_change_expected']
    daily_bests = forecasts[idx]
    total_performance = calc_composite_strategy_performance(daily_bests, None)
    last_month_performance = calc_composite_strategy_performance(daily_bests, 30)
    last_week_performance = calc_composite_strategy_performance(daily_bests, 7)
    last_day_performance = calc_composite_strategy_performance(daily_bests, 1)
    logger.info(f"done running performance calculations")
    return pd.DataFrame(data={'total_performance': [total_performance],
                              'last_timestamp_reported': [forecasts['last_timestamp_reported'].max() + pd.Timedelta(days=1)],
                              'last_month_performance': [last_month_performance],
                              'last_week_performance': [last_week_performance],
                              'last_day_performance': [last_day_performance],
                              'hold_performance': [pd.NA],
                              'total_days': [len(forecasts['last_timestamp_reported'].unique())],
                              'coin': 'RH Composite',
                              'p': p,
                              'd': d,
                              'q': q})


def calc_composite_strategy_performance(df: pd.DataFrame, period):
    if period is not None and period < len(df):
        df = df.tail(period)
    investment = 100
    for i, row in df.iterrows():
        if row['next_day_pct_change_expected'] > 0:
            investment = investment * (1 + row['next_day_pct_change_actual'] / 100)
    return investment - 100


def calc_period_change(df, period):
    if period is not None and period < len(df):
        df = df.tail(period)
    investment = 100
    for i, row in df.iterrows():
        investment = calc_value_change(row['last_close'], row['next_day_price'], row['next_day_actual'], investment)
    return investment - 100


def calc_value_change(starting_price, predicted_price, ending_price, investment):
    if predicted_price < starting_price:
        return investment  # if we predict a loss, don't invest
    return (ending_price / starting_price) * investment


def save_predictions_for_coin(last_close, next_day_price, seven_day_price, coin, last_timestamp_reported, p, d, q):
    crypto_predictions_arima_repo.save_predictions_for_coin(last_close, next_day_price, seven_day_price, coin,
                                                            last_timestamp_reported, p, d, q)


def fetch_up_to_date_daily_data(coin: str):
    data = fetch_price_hist_from_db(coin)
    if not is_price_hist_up_to_date(data):
        logger.info("db not up to date")
        new_data = fetch_daily_data_from_coinbase(coin)
        update_coin_price_hist(new_data, data)
        return new_data
    else:
        logger.info("db up to date")
    return data


def update_coin_price_hist(new_data: pd.DataFrame, data: pd.DataFrame):
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
        conn.close()


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


def fetch_price_hist_from_db(coin: str):
    conn = get_connection()
    data = pd.read_sql(sql.text(f"select coin, open, high, low, close, date, vol_fiat, volume"
                                f" from crypto_prices where coin = '{coin}'"), conn)
    conn.commit()
    conn.close()
    return data


def is_price_hist_up_to_date(data: pd.DataFrame):
    if data is None or data.empty:
        return False
    db_date = data['date'].max().tz_localize(None)
    now_gmt = pd.Timestamp.now(tz='GMT').tz_localize(None)
    yesterday = now_gmt - pd.Timedelta(days=1)
    return db_date > yesterday


def predict_next_7(hist_data: pd.DataFrame, p, d, q):
    close_data = hist_data[['date', 'close']]
    close_data = close_data.sort_values(by='date')
    close_data = close_data.set_index('date')
    close_data_log = np.log(close_data)
    close_data_log.dropna(inplace=True)
    model = ARIMA(np.asarray(close_data_log), order=(p, d, q))
    results = model.fit()
    forecast = pd.DataFrame(data={"close": results.forecast(steps=7)})
    last_day = close_data_log.index.to_series().iloc[-1]
    forecast['date'] = [datetime.timedelta(days=i) + last_day for i in range(1, 8)]
    data_plus_forecast = pd.concat([close_data_log.reset_index(None), forecast])
    data_plus_forecast['close'] = np.exp(data_plus_forecast['close'])
    data_plus_forecast = data_plus_forecast.sort_values(by='date')
    return data_plus_forecast


def testlog(msg):
    file_handler = logging.FileHandler('output.log')
    handler = logging.StreamHandler()
    file_handler.setLevel(logging.DEBUG)
    handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))
    app.logger.addHandler(handler)
    app.logger.addHandler(file_handler)
    app.logger.error(msg)


if __name__ == '__main__':
    app.run(port=5002, debug=True)
