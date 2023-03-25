import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
sns.set()

from sklearn.metrics import r2_score, median_absolute_error, mean_absolute_error
from sklearn.metrics import median_absolute_error, mean_squared_error, mean_squared_log_error

from scipy.optimize import minimize
import statsmodels.tsa.api as smt
import statsmodels.api as sm

from tqdm import tqdm_notebook

from itertools import product

def mean_absolute_percentage_error(y_true, y_pred):
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

import warnings
warnings.filterwarnings('ignore')

DATAPATH = 'data/island-data-bottle-round-3/island-data-bottle-round-3/prices_round_3_day_0.csv'

data = pd.read_csv(DATAPATH, delimiter=';', index_col=['timestamp'])
drop_cols = ['day', 'profit_and_loss']
#data.drop(drop_cols, axis=1, inplace=True)
bid_prices = ['bid_price_1', 'bid_price_2', 'bid_price_3']
bid_volumes = ['bid_volume_1', 'bid_volume_2', 'bid_volume_3']
ask_prices = ['ask_price_1', 'ask_price_2', 'ask_price_3']
ask_volumes = ['ask_volume_1', 'ask_volume_2', 'ask_volume_3']
data.fillna(value = 0, inplace=True)

data['bid_weighted_avg'] = (data[bid_prices] * data[bid_volumes]).sum(axis=1) / data[bid_volumes].sum(axis=1)
data['ask_weighted_avg'] = (data[bid_prices] * data[bid_volumes]).sum(axis=1) / data[bid_volumes].sum(axis=1)


pearls = data[data['product'] == 'PEARLS']
bananas = data[data['product'] == 'BANANAS']
berries = data[data['product'] == 'BERRIES']

train = berries[berries.index < 900000].mid_price
test = berries[berries.index >= 900000].mid_price
train.index = train.index/100
test.index = test.index/100

plt.plot(train, color = "black")
plt.plot(test, color = "red")
plt.ylabel('BTC Price')
plt.xlabel('Date')
plt.xticks(rotation=45)
plt.title("Train/Test split for BTC Data")
plt.show()

# Set initial values and some bounds
ps = range(0, 5)
d = 1
qs = range(0, 5)
Ps = range(0, 5)
D = 1
Qs = range(0, 5)
s = 5

# Create a list with all possible combinations of parameters
parameters = product(ps, qs, Ps, Qs)
parameters_list = list(parameters)
len(parameters_list)


# Train many SARIMA models to find the best set of parameters
def optimize_SARIMA(parameters_list, d, D, s):
    """
        Return dataframe with parameters and corresponding AIC

        parameters_list - list with (p, q, P, Q) tuples
        d - integration order
        D - seasonal integration order
        s - length of season
    """

    results = []
    best_aic = float('inf')

    for param in tqdm_notebook(parameters_list):
        try:
            model = sm.tsa.statespace.SARIMAX(train, order=(param[0], d, param[1]),
                                              seasonal_order=(param[2], D, param[3], s)).fit(disp=-1)
        except:
            continue

        aic = model.aic

        # Save best model, AIC and parameters
        if aic < best_aic:
            best_model = model
            best_aic = aic
            best_param = param
        results.append([param, model.aic])

    result_table = pd.DataFrame(results)
    result_table.columns = ['parameters', 'aic']
    # Sort in ascending order, lower AIC is better
    result_table = result_table.sort_values(by='aic', ascending=True).reset_index(drop=True)

    return result_table


result_table = optimize_SARIMA(parameters_list, d, D, s)

# Set parameters that give the lowest AIC (Akaike Information Criteria)
p, q, P, Q = result_table.parameters[0]

best_model = sm.tsa.statespace.SARIMAX(train, order=(p, d, q),
                                       seasonal_order=(P, D, Q, s)).fit(disp=-1)

print(best_model.summary())
