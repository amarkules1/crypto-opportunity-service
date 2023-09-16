import pandas as pd
import sqlalchemy
from cachetools import cached, LRUCache, TTLCache
from repos.db_utils import get_connection


class CryptoPredictionsArimaRepository:
    all_data: pd.DataFrame = None

    conn = None

    def __init__(self):
        self.conn = get_connection()
        self.all_data = pd.read_sql(sqlalchemy.text(f"select * from crypto_predictions_arima"), self.conn)
        self.conn.commit()

    @cached(cache=LRUCache(maxsize=None))
    def get_coin_forecasts_with_actual(self, coin: str, p: int, d: int, q: int):
        forecasts = self.all_data[self.all_data['coin'] == coin]
        forecasts = forecasts[forecasts['p'] == p]
        forecasts = forecasts[forecasts['d'] == d]
        forecasts = forecasts[forecasts['q'] == q]
        forecasts = forecasts.sort_values(by='last_timestamp_reported')
        forecasts['next_day_actual'] = forecasts['last_close'].shift(-1)
        return forecasts.dropna(subset=['next_day_actual'])

    def save_predictions_for_coin(self, last_close, next_day_price, seven_day_price, coin, last_timestamp_reported, p,
                                  d, q):
        # determine if prediction for day, coin, pdq already exists
        existing = self.all_data[self.all_data['last_timestamp_reported'] == last_timestamp_reported]
        existing = existing[existing['coin'] == coin]
        existing = existing[existing['p'] == p]
        existing = existing[existing['d'] == d]
        existing = existing[existing['q'] == q]
        if len(existing) < 1:
            # may need to spin up a separate thread for this...
            self.conn.execute(sqlalchemy.text(
                f"insert into crypto_predictions_arima"
                f"(last_close, next_day_price, seven_day_price, coin, last_timestamp_reported, p, d, q) "
                f"values({last_close},{next_day_price},{seven_day_price},'{coin}','{last_timestamp_reported}', "
                f"{p}, {d}, {q})"))
            self.conn.commit()
            # add to in-mem df
            self.all_data = self.all_data.append({'last_close': last_close,
                                                  'next_day_price': next_day_price,
                                                  'seven_day_price': seven_day_price,
                                                  'coin': coin,
                                                  'last_timestamp_reported': last_timestamp_reported,
                                                  'p': p,
                                                  'd': d,
                                                  'q': q}, ignore_index=True)

    def get_data_for_last_day(self):
        return self.all_data[self.all_data['last_timestamp_reported'] == self._get_last_timestamp_reported()]

    def _get_last_timestamp_reported(self):
        return self.all_data['last_timestamp_reported'].max()


