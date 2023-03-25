from statistics import mean, median
import numpy as np
import pandas as pd
from typing import Dict, List
import matplotlib.pyplot as plt

class CocoPinaCls:
    def __init__(self):
        self.limits = {
          "COCONUTS": 600,
          "PINA_COLADAS": 300
        }
        self.beta = 0.5332239509498264
        
    def __call__(self, states : List[Dict]):
        last_state = states[-1]
        order_depths = last_state.order_depths
        # calculate mid price of COCONUTS
        orders_coco = order_depths['COCONUTS']
        coco_buys = orders_coco.buy_orders
        buys = []
        for buy_price, volume in coco_buys:
            buys += [buy_price] * volume
        median_price_buys = median(buys)
        coco_sells = orders_coco.sell_orders
        sells = []
        for sell_price, volume in coco_sells:
            sells += [sell_price] * (-volume)
        median_price_sells = median(sells)
        coco = mean([median_price_buys, median_price_sells])
        
        # calculate mid price of PINA_COLADAS
        orders_pina = order_depths['PINA_COLADAS']
        pina_buys = orders_pina.buy_orders
        buys = []
        for buy_price, volume in pina_buys:
            buys += [buy_price] * volume
        median_price_buys = median(buys)
        pina_sells = orders_pina.sell_orders
        sells = []
        for sell_price, volume in pina_sells:
            sells += [sell_price] * (-volume)
        median_price_sells = median(sells)
        pina = mean([median_price_buys, median_price_sells])
        
        # calculate spread
        spread = coco - self.beta * pina
        
        # if spread is negative, PINA_COLADAS are overpriced, otherwise COCONUTS are
        if spread < 0:
            # long cocos, short pinas, go BOLD
            return {'COCONUTS': self.limits['COCONUTS'], 'PINA_COLADAS': -self.limits['PINA_COLADAS']}
        else:
            return {'COCONUTS': -self.limits['COCONUTS'], 'PINA_COLADAS': self.limits['PINA_COLADAS']}
      
if __name__ == "__main__":
    data_neg1 = pd.read_csv('data/prices_round_2_day_-1.csv', sep=';')
    data_0 = pd.read_csv('data/prices_round_3_day_0.csv', sep=';')
    data_1 = pd.read_csv('data/prices_round_3_day_1.csv', sep=';')
    data_2 = pd.read_csv('data/prices_round_3_day_2.csv', sep=';')
    
    data = pd.concat([data_neg1, data_0, data_1, data_2])
    data_coco = data[data['product'] == 'COCONUTS']['mid_price'].to_numpy()
    data_pina = data[data['product'] == 'PINA_COLADAS']['mid_price'].to_numpy()
    
    plt.plot(data_coco + 7000)
    plt.plot(data_pina)
    plt.show()
    
    beta, _, _, _ = np.linalg.lstsq(data_pina[:, np.newaxis], data_coco)
    print(beta[0])
    
    plt.plot(data_coco - beta[0] * data_pina)
    plt.show()
    
    