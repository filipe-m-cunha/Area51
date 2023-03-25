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
        self.beta = 0.5332246610399421
        
        self.lag = 5
        self.slope_lag = 5
        self.spreads = []
        self.time = 0
        
    def __call__(self, states : List[Dict]):
        pina_state = states[-1]
        
        if self.time >= self.lag:
            coco_state = states[-1 - self.lag] 
        else:
            coco_state = pina_state
        
        coco_depths = coco_state.order_depths
        # calculate mid price of COCONUTS
        orders_coco = coco_depths['COCONUTS']
        coco_buys = orders_coco.buy_orders
        buys = []
        for buy_price in coco_buys.keys():
            buys += [buy_price] * coco_buys[buy_price]
        median_price_buys = median(buys)
        coco_sells = orders_coco.sell_orders
        sells = []
        for sell_price in coco_sells.keys():
            sells += [sell_price] * (-coco_sells[sell_price])
        median_price_sells = median(sells)
        coco = mean([median_price_buys, median_price_sells])
        
        pina_depths = pina_state.order_depths
        # calculate mid price of PINA_COLADAS
        orders_pina = pina_depths['PINA_COLADAS']
        pina_buys = orders_pina.buy_orders
        buys = []
        for buy_price in pina_buys.keys():
            buys += [buy_price] * pina_buys[buy_price]
        median_price_buys = median(buys)
        pina_sells = orders_pina.sell_orders
        sells = []
        for sell_price in pina_sells.keys():
            sells += [sell_price] * (-pina_sells[sell_price])
        median_price_sells = median(sells)
        pina = mean([median_price_buys, median_price_sells])
        
        # calculate spread
        spread = coco - self.beta * pina
        if self.spreads == [] or self.spreads[-1] != spread:
            self.spreads.append(spread)
            self.time += 1
            
        if self.time >= 30 and self.time % 5 == 0 and spread < 0 and spread - self.spreads[-5] < 0:
            return {'COCONUTS': -300, 'PINA_COLADAS': 0}
        elif self.time >= 30 and self.time % 5 == 0 and spread > 0 and spread - self.spreads[-5] > 0:
            return {'COCONUTS': 0, 'PINA_COLADAS': -300}
        
        # if spread is negative, PINA_COLADAS are overpriced, otherwise COCONUTS are
        if spread < 0:
            # long cocos, short pinas, go BOLD
            if abs(spread) > 20:
                return {'COCONUTS': 10, 'PINA_COLADAS': -10}
            else:
                return {'COCONUTS': 5, 'PINA_COLADAS': -5}
        else:
            if abs(spread) > 20:
                return {'COCONUTS': -10, 'PINA_COLADAS': 10}
            else:
                return {'COCONUTS': -50, 'PINA_COLADAS': 5}
      
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
    
    beta, _, _, _ = np.linalg.lstsq(data_pina[5:, np.newaxis], data_coco[:-5])
    print(beta[0])
    
    plt.plot(data_coco - beta[0] * data_pina)
    plt.show()
    
    