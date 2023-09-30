import numpy as np
from statsmodels.tsa.arima.model import ARIMA


def backtest_buy_sell_performance(data, p, d, q, prediction_days):
    tests = len(data) - prediction_days
    perf = 0
    for i in range(tests):
        # get the right slice of data
        test_data = data.iloc[i:i + prediction_days]
        if get_next_day_buy_signal(test_data, p, d, q):
            actual_price = data['close'].iloc[i + prediction_days]
            last_day_close = test_data['close'].iloc[-1]
            perf += actual_price - last_day_close
    return (perf/data.iloc[prediction_days - 1]['close']) * 100


def get_next_day_buy_signal(data, p, d, q):
    data.sort_values(by='date')
    next_day_prediction = get_prediction(data, p, d, q, 1)
    last_day_close = data['close'].iloc[-1]
    return next_day_prediction > last_day_close


def get_prediction(data, p, d, q, days_out):
    train = data.copy(deep=True)[['date', 'close']]
    train = train.sort_values(by='date')
    train = train.set_index('date')
    train_log = np.log(train)
    train_log.dropna(inplace=True)
    model = ARIMA(np.asarray(train_log), order=(p, d, q))
    results = model.fit()
    return np.exp(results.forecast(steps=days_out)[-1])

