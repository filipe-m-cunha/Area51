from typing import Dict, List
from copy import deepcopy
import numpy as np
from statistics import mean, median
from datamodel import OrderDepth, TradingState, Order

COMMODITIES = ["BANANAS", "COCONUTS", "PINA_COLADAS", "DIVING_GEAR", "BERRIES"]
POSITION_LIMITS = {"PEARLS": 20, "BANANAS": 20, "COCONUTS":600, "PINA_COLADAS": 300, "DIVING_GEAR": 50, "BERRIES": 250}
PRINT_PEARL = False
PRINT_PRODUCTS = {"BANANAS": True, "COCONUTS": True, "PINA_COLADAS": True, "BERRIES": True, "DIVING_GEAR": True}
STAT_SLIDING_WINDOW_SIZE = 7

# [CLOSE LONG, OPEN SHORT, CLOSE SHORT, OPEN LONG]
CAN_LONG = {"BANANAS": True, "COCONUTS": True, "PINA_COLADAS": False, "BERRIES": True, "DIVING_GEAR": True}
CAN_SHORT = {"BANANAS": True, "COCONUTS": False, "PINA_COLADAS": True, "BERRIES": False, "DIVING_GEAR": False}

BUY_MARGIN = {"BANANAS": 1, "BERRIES": 1}
SELL_MARGIN = {"BANANAS": 1, "BERRIES": 1}

INITIAL_CONDITIONS = [
    lambda price, slw_bid, slw_ask, positions, volume, time: price > np.mean(np.array(positions[:volume]))\
        or np.mean(np.array(time[:volume])) > 150,
    lambda price, slw_bid, slw_ask, positions, volume, time: price > slw_ask.get_percentile(10)-2 \
        and slw_ask.length() > 2,
    lambda price, slw_bid, slw_ask, positions, volume, time: price < np.mean(np.array(positions[:volume]))\
        or np.mean(np.array(time[:volume])) > 180,
    lambda price, slw_bid, slw_ask, positions, volume, time: price <= slw_bid.get_percentile(90) \
        and slw_bid.length() > 2]


# [CLOSE LONG, OPEN SHORT, CLOSE SHORT, OPEN LONG]
DECISION_CONDITIONS = {"BANANAS": INITIAL_CONDITIONS, "COCONUTS": INITIAL_CONDITIONS, "PINA_COLADAS": INITIAL_CONDITIONS, "BERRIES": INITIAL_CONDITIONS, "DIVING_GEAR": INITIAL_CONDITIONS}
DECISION_CONDITIONS["DIVING_GEAR"] = [
    lambda price, slw_bid, slw_ask, positions, volume, time: price > np.mean(np.array(positions[:volume]))\
        or np.mean(np.array(time[-volume:])) > 10000,
    lambda price, slw_bid, slw_ask, positions, volume, time: price > slw_bid.get_percentile(50) \
        and slw_ask.length() > 2,
    lambda price, slw_bid, slw_ask, positions, volume, time: price < np.mean(np.array(positions[:volume]))\
        or np.mean(np.array(time[:volume])) > 5000,
    lambda price, slw_bid, slw_ask, positions, volume, time: price <= slw_ask.get_percentile(50) \
        and slw_bid.length() > 2]
DECISION_CONDITIONS["BERRIES"] = [
    lambda price, slw_bid, slw_ask, positions, volume, time: price > np.mean(np.array(positions[:volume]))\
        or np.mean(np.array(time[-volume:])) > 10000,
    lambda price, slw_bid, slw_ask, positions, volume, time: price > slw_bid.get_percentile(50) \
        and slw_ask.length() > 2,
    lambda price, slw_bid, slw_ask, positions, volume, time: price < np.mean(np.array(positions[:volume]))\
        or np.mean(np.array(time[:volume])) > 5000,
    lambda price, slw_bid, slw_ask, positions, volume, time: price <= slw_ask.get_percentile(50) \
        and slw_bid.length() > 2]



class Trader:

    def __init__(self):
        self.sliding_window_size = STAT_SLIDING_WINDOW_SIZE
        self.product_stats = {}
        self.sliding_window_means = []
        self.limits = {"PEARLS": 20, "BANANAS": 20, "COCONUTS": 600, "PINA_COLADAS": 300, "DIVING_GEAR": 50,
                           "BERRIES": 250}
        
        cumulative_profit = { c:0 for c in COMMODITIES }

        
        # JOHAN
        self.states : List[Dict] = []
        self.time : int = 0
        self.hard_limit = False

        self.johan_short_positions = { c:[] for c in COMMODITIES}
        self.johan_long_positions = { c:[] for c in COMMODITIES}
        self.cumulative_profit = { c:0 for c in COMMODITIES}
        self.johan_can_trade = { c:True for c in COMMODITIES}

    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        # Initialize the method output dict as an empty dict
        result = {}

        # Vu initializations

        # JOHAN
        # Compute changes in state
        position = deepcopy(state.position)
        for product in state.order_depths.keys():
            if not product in position:
                position[product] = 0

        self.states.append(state)
        
        coco_pina_cls = CocoPinaCls()

        # Iterate over all the keys (the available products) contained in the order depths
        for product in state.order_depths.keys():


            # Check if the current product is the 'PEARLS' product, only then run the order logic
            if product == 'PEARLS':
                # Retrieve the Order Depth containing all the market BUY and SELL orders for PEARLS
                order_depth: OrderDepth = state.order_depths[product]

                # Initialize the list of Orders to be sent as an empty list
                orders: list[Order] = []
                acceptable_price = 10000

                if len(order_depth.sell_orders) > 0:
                    # Sort and check whether any orders
                    for ask_price in [sorted(order_depth.sell_orders.keys())[0]]:
                        if ask_price >= acceptable_price + 1:
                            break
                        if ask_price < acceptable_price:
                            ask_volume = order_depth.sell_orders[ask_price]
                            print("BUY PEARLS", str(-ask_volume) + "x", ask_price)
                            orders.append(Order(product, ask_price, -ask_volume))
                        else:
                            ask_volume = POSITION_LIMITS[product] // 4
                            orders.append(Order(product, ask_price, -ask_volume))
                if len(order_depth.buy_orders) != 0:
                    for ask_price in [sorted(order_depth.buy_orders.keys(), reverse=True)[0]]:
                        if ask_price <= acceptable_price - 1:
                            break
                        if ask_price <= acceptable_price:
                            ask_volume = order_depth.buy_orders[ask_price]
                            print("SELL PEARLS", str(ask_volume) + "x", ask_price)
                            orders.append(Order(product, ask_price, -ask_volume))
                        else:
                            ask_volume = POSITION_LIMITS[product] // 4
                            print("SELL PEARLS", str(ask_volume) + "x", ask_price)
                            orders.append(Order(product, ask_price, -ask_volume))
                result[product] = orders
            elif product == 'PINA_COLADAS' or product == 'COCONUTS':
                # MAX / JOHAN
                diffs = coco_pina_cls(self.states)
                if diffs is None or not product in diffs:
                    continue

                diff = diffs[product]
                if abs(position[product] + diff) > self.limits[product]:
                    if self.hard_limit:
                        raise Exception(f"Position limit exceeded for {product}: old_position={position[product]}, diff={diff}")
                    else:
                        diff = max(diff, -self.limits[product] - position[product])
                        diff = min(diff, self.limits[product] - position[product])
                        diffs[product] = diff
            
                if diff > 0 and self.johan_can_trade[product]:
                    result[product] = self.buy(product, diff, state.order_depths[product])
                elif diff < 0 and self.johan_can_trade[product]:
                    result[product] = self.sell(product, -diff, state.order_depths[product])
                    
                    
            elif product == 'DOLPHIN_SIGHTINGS':
                # TODO: use dolphin knowledge, DOLPHIN_SIGHTINGS is not a tradable good!
                continue
            elif product == 'BERRIES' or product == 'BANANAS': #! this is now for BANANAS and BERRIES rn
                if product not in self.product_stats.keys():
                    sliding_window_ask = SlidingWindowStatistics(STAT_SLIDING_WINDOW_SIZE, str(product) + "_ASK")
                    sliding_window_bid = SlidingWindowStatistics(STAT_SLIDING_WINDOW_SIZE, str(product) + "_BID")
                    self.product_stats[product] = [sliding_window_ask, sliding_window_bid, {
                        'bid_hist': [],
                        'ask_hist': [],
                        'ask_price': [],
                        'bid_price': []
                    }, [], [], [], []]

                order_depth: OrderDepth = state.order_depths[product]
                orders: list[Order] = []

                sliding_window_ask = self.product_stats[product][0]
                sliding_window_bid = self.product_stats[product][1]
                best_prices = self.product_stats[product][2]
                long_positions = self.product_stats[product][3]
                short_positions = self.product_stats[product][4]
                long_time = self.product_stats[product][5]
                short_time = self.product_stats[product][6]

                if PRINT_PRODUCTS[product]:
                    sliding_window_ask.add(order_depth.sell_orders)
                    sliding_window_bid.add(order_depth.buy_orders)

                if len(order_depth.sell_orders) > 0:
                    ask_price = list(sorted(order_depth.sell_orders.keys()))[0]
                    best_prices['ask_price'].append(ask_price)
                    if len(best_prices['ask_price']) > STAT_SLIDING_WINDOW_SIZE:
                        best_prices['ask_price'].pop(0)

                if len(order_depth.buy_orders) > 0:
                    bid_price = list(sorted(order_depth.buy_orders.keys(), reverse=True))[0]
                    best_prices['bid_price'].append(bid_price)
                    if len(best_prices['bid_price']) > STAT_SLIDING_WINDOW_SIZE:
                        best_prices['bid_price'].pop(0)

                curr_value = 0.5* sum([sum(best_prices[val]) / len(best_prices[val]) for val in ['ask_price', 'bid_price']])

                if ask_price:
                    if ask_price < curr_value:
                        ask_volume = order_depth.sell_orders[ask_price]
                        orders.append(Order(product, ask_price, -ask_volume))
                        short_positions += [ask_price for i in range(abs(ask_volume))]
                    if ask_price - curr_value/5000 > curr_value:
                        orders.append(Order(product, ask_price - (int(curr_value/5000)+1), -POSITION_LIMITS[product]//4))
                        short_positions += [ask_price for i in range(abs(POSITION_LIMITS[product]//4))]
                    if ask_price > curr_value:
                        orders.append(Order(product, ask_price, -POSITION_LIMITS[product]//4))
                        short_positions += [ask_price for i in range(abs(POSITION_LIMITS[product]//4))]

                if bid_price:
                    if bid_price > curr_value:
                        bid_volume = order_depth.buy_orders[bid_price]
                        orders.append(Order(product, bid_price, -bid_volume))
                        long_positions += [ask_price for i in range(abs(bid_volume))]

                    if bid_price + curr_value/5000 < curr_value:
                        orders.append(Order(product, bid_price + (int(curr_value/5000)+1), POSITION_LIMITS[product] // 4))
                        long_positions += [ask_price for i in range(abs(POSITION_LIMITS[product] // 4))]
                    if bid_price < curr_value:
                        orders.append(Order(product, bid_price, POSITION_LIMITS[product] // 4))
                        long_positions += [ask_price for i in range(abs(POSITION_LIMITS[product] // 4))]

                short_time = list(map(lambda n: n+1, short_time))
                long_time = list(map(lambda n: n+1, long_time))

                self.product_stats[product][0] = sliding_window_ask
                self.product_stats[product][1] = sliding_window_bid
                self.product_stats[product][2] = best_prices
                self.product_stats[product][3] = long_positions
                self.product_stats[product][4] = short_positions
                self.product_stats[product][5] = long_time
                self.product_stats[product][6] = short_time

                # Add all the above orders to the result dict
                result[product] = orders
            elif product == 'DIVING_GEAR':
                if product not in self.product_stats.keys():
                    sliding_window_ask = SlidingWindowStatistics(STAT_SLIDING_WINDOW_SIZE, str(product) + "_ASK")
                    sliding_window_bid = SlidingWindowStatistics(STAT_SLIDING_WINDOW_SIZE, str(product) + "_BID")
                    self.product_stats[product] = [sliding_window_ask, sliding_window_bid, [], [], [], []]

                order_depth: OrderDepth = state.order_depths[product]
                orders: list[Order] = []

                sliding_window_ask = self.product_stats[product][0]
                sliding_window_bid = self.product_stats[product][1]
                long_positions = self.product_stats[product][2]
                short_positions = self.product_stats[product][3]
                long_time = self.product_stats[product][4]
                short_time = self.product_stats[product][5]

                def update_long_short():
                    # if len(short_positions) > 0:
                    #     CAN_LONG[product] = False
                    #     CAN_SHORT[product] = True
                    # if len(short_positions) == 0:
                    #     CAN_SHORT[product] = True
                    #     CAN_LONG[product] = False
                    # if len(long_positions) > 0:
                    #     CAN_SHORT[product] = False
                    #     CAN_LONG[product] = True
                    # if len(short_positions) == 0:
                    #     CAN_LONG[product] = True
                    #     CAN_SHORT[product] = False
                    pass


                if PRINT_PRODUCTS[product]:
                    sliding_window_ask.add(order_depth.sell_orders)
                    sliding_window_bid.add(order_depth.buy_orders)

                if len(order_depth.buy_orders) > 0:
                    num_long_positions = len(long_positions)
                    num_short_positions = len(short_positions)
                    can_short = True
                    print("bot bid depths: ", str(order_depth.buy_orders))

                    # CLOSE LONG
                    for bid_price in sorted(order_depth.buy_orders.keys(), reverse=True):
                        bid_volume = min(order_depth.buy_orders[bid_price], num_long_positions)
                        # if bid_price > np.mean(np.array(long_positions[:bid_volume])) \
                        #     or np.mean(np.array(long_time[:bid_volume])) > 150 and can_long:
                        if DECISION_CONDITIONS[product][0](bid_price, sliding_window_bid, sliding_window_ask,\
                            long_positions, bid_volume, long_time):
                            print(f"SELL {product} LONG", str(bid_volume) + "x", bid_price)
                            orders.append(Order(product, bid_price, -bid_volume))
                            num_long_positions -= bid_volume
                            long_positions = long_positions[bid_volume:]
                            long_time = long_time[bid_volume:]
                            update_long_short()

                    # OPEN SHORT
                    for bid_price in sorted(order_depth.buy_orders.keys()):
                        bid_volume = min(order_depth.buy_orders[bid_price], POSITION_LIMITS[product] - num_short_positions)
                        # if bid_price > sliding_window_ask.get_percentile(10) - 2 and len(
                        #         sliding_window_ask.sliding_window) > 2 and can_short:
                        if DECISION_CONDITIONS[product][1](bid_price, sliding_window_bid, sliding_window_ask,\
                            short_time, bid_volume, short_time) and CAN_SHORT[product]:
                            print(f"SELL {product} SHORT", str(bid_volume) + "x", bid_price)
                            orders.append(Order(product, bid_price, -bid_volume))
                            num_short_positions += abs(bid_volume)
                            short_positions += [bid_price for x in range(abs(bid_volume))]
                            short_time += [0 for x in range(abs(bid_volume))]
                            update_long_short()

                if len(order_depth.sell_orders) > 0:
                    num_long_positions = len(long_positions)
                    num_short_positions = len(short_positions)
                    can_short = True
                    can_long = True

                    # CLOSE SHORT
                    for ask_price in sorted(order_depth.sell_orders.keys(), reverse=True):
                        ask_volume = max(order_depth.sell_orders[ask_price], -(num_short_positions))
                        # bug: should do abs(ask_volume), but nothing has beaten this...
                        # if ask_price < np.mean(np.array(short_positions[:ask_volume])) - 2 \
                        #     or np.mean(np.array(short_time[:ask_volume])) > 180 and can_short:
                        if DECISION_CONDITIONS[product][2](ask_price, sliding_window_bid, sliding_window_ask,\
                            short_positions, ask_volume, short_time):
                            print(f"BUY {product} SHORT", str(-ask_volume) + "x", ask_price)
                            orders.append(Order(product, ask_price, -ask_volume))
                            num_short_positions -= ask_volume
                            short_positions = short_positions[abs(ask_volume):]
                            short_time = short_time[abs(ask_volume):]
                            update_long_short()

                    # OPEN LONG
                    print("bot ask depths: " + str(order_depth.sell_orders))
                    for ask_price in sorted(order_depth.sell_orders.keys()):
                        ask_volume = max(order_depth.sell_orders[ask_price], -(POSITION_LIMITS[product] - (num_long_positions)))
                        # if ask_price <= sliding_window_bid.get_percentile(90) and len(
                        #     sliding_window_bid.sliding_window) > 2 and can_long:
                        if DECISION_CONDITIONS[product][3](ask_price, sliding_window_bid, sliding_window_ask,\
                            long_positions, ask_volume, long_time) and CAN_LONG[product]:
                            print(f"BUY {product} LONG", str(-ask_volume) + "x", ask_price)
                            orders.append(Order(product, ask_price, -ask_volume))
                            num_long_positions -= ask_volume
                            long_positions += [ask_price for x in range(abs(ask_volume))]
                            long_time += [0 for x in range(abs(ask_volume))]
                            update_long_short()

                short_time = list(map(lambda n: n+1, short_time))
                long_time = list(map(lambda n: n+1, long_time))

                self.product_stats[product][0] = sliding_window_ask
                self.product_stats[product][1] = sliding_window_bid
                self.product_stats[product][2] = long_positions
                self.product_stats[product][3] = short_positions
                self.product_stats[product][4] = long_time
                self.product_stats[product][5] =  short_time

                

                # Add all the above orders to the result dict
                result[product] = orders


        for product in self.product_stats.keys():

            if product not in ['PEARLS', 'DOLPHIN_SIGHTINGS']:

                if state.timestamp % (self.sliding_window_size * 2 * 100) == 0:
                    self.sliding_window_means.append(self.product_stats[product][0].get_mean())

                #print(state.position)
                #print(self.product_stats[product][2])
                #print(self.product_stats[product][3])

                # Print stats
                if PRINT_PRODUCTS[product]:
                    self.product_stats[product][0].print_stats()
                    self.product_stats[product][1].print_stats()
        # JOHAN
        self.time += 1

        if self.cumulative_profit["COCONUTS"] > 9000:
            self.johan_can_trade["COCONUTS"] = False


        return result

    # JOHAN
    def buy(self, product : str, n : int, order_depth):

        # Iterate over offers
        orders = []
        for ask_price in sorted(order_depth.sell_orders.keys()):
            
            # Compute volume for one trade
            ask_volume = -order_depth.sell_orders[ask_price]
            curr_volume = min(n, ask_volume)

            # print("Sell orders :", order_depth.sell_orders)
            # print("Buy", product, ask_volume, n, curr_volume, ask_price, Order(product, ask_price, curr_volume))
            remaining_buy_quantity = abs(curr_volume)

            # close short
            if len(self.johan_short_positions[product]) > 0:
                short_close_quantity = min(len(self.johan_short_positions[product]), remaining_buy_quantity)
                self.cumulative_profit[product] += sum(self.johan_short_positions[product][:short_close_quantity]) - short_close_quantity * ask_price
                self.johan_short_positions[product] = self.johan_short_positions[product][short_close_quantity:]
                remaining_buy_quantity -= short_close_quantity

            # open long
            if len(self.johan_short_positions[product]) == 0 and remaining_buy_quantity > 0:
                self.johan_long_positions[product].extend([ask_price for x in range(remaining_buy_quantity)])
                remaining_buy_quantity = 0

            
            # Place order
            orders.append(Order(product, ask_price, curr_volume))

            # Update volume needed
            n -= curr_volume
            if n == 0:
                break
        return orders

    # JOHAN
    def sell(self, product : str, n : int, order_depth):

        # Iterate over offers
        orders = []
        for bid_price in sorted(order_depth.buy_orders.keys(), reverse=True):
            
            # Compute volume for one trade
            bid_volume = order_depth.buy_orders[bid_price]
            curr_volume = min(n, bid_volume)

            # print("Buy orders :", order_depth.buy_orders)
            # print("Sell", product, bid_volume, n, curr_volume, bid_price, Order(product, bid_price, -curr_volume))
            
            remaining_sell_quantity = abs(curr_volume)
            # close long
            if len(self.johan_long_positions[product]) > 0:
                long_close_quantity = min(len(self.johan_long_positions[product]), remaining_sell_quantity)
                self.cumulative_profit[product] += long_close_quantity * bid_price - sum(self.johan_long_positions[product][:long_close_quantity])
                self.johan_long_positions[product] = self.johan_long_positions[product][long_close_quantity:]
                remaining_sell_quantity -= long_close_quantity
            # open short
            if len(self.johan_long_positions[product]) == 0:
                self.johan_short_positions[product].extend([bid_price for x in range(remaining_sell_quantity)])
                remaining_sell_quantity = 0

            # Place order
            orders.append(Order(product, bid_price, -curr_volume))

            # Update volume needed
            n -= curr_volume
            if n == 0:
                break

        return orders


class SlidingWindowStatistics:

    def __init__(self, sliding_window_size, statistics_type):
        self.sliding_window_size = sliding_window_size
        self.sliding_window = []
        self.statistics_type = statistics_type
        self.mean = 10000
        self.flat_list = []

    def add(self, order_depth):
        self.sliding_window.append(order_depth)
        if len(self.sliding_window) > self.sliding_window_size:
            self.sliding_window = self.sliding_window[-self.sliding_window_size:]

    # Outputs flat sorted list of orders in the sliding window
    def flatten(self):
        flat_list = []
        for order_depth_dict in self.sliding_window:
            for price in order_depth_dict:
                flat_list.extend([price for x in range(abs(order_depth_dict[price]))])

        flat_list.sort()
        return flat_list

    def should_act(self, curr_price, buy=True):
        order_depth_dict = self.sliding_window[0]
        if buy:
            min_momentum_price = np.mean(np.array([price for price in order_depth_dict]))
        else:
            min_momentum_price = max([price for price in order_depth_dict])
        momentum = curr_price - min_momentum_price
        if momentum > 0:
            return True
        else:
            return False

    def update_stats(self):
        self.flat_list = self.flatten()
        self.mean = np.mean(np.array(self.flat_list))

    def get_mean(self):
        return self.mean

    def get_min(self):
        if len(self.flat_list) > 0:
            return self.flat_list[0]
        else:
            return 0

    def get_max(self):
        if len(self.flat_list) > 0:
            return self.flat_list[-1:][0]
        else:
            return 0

    def get_percentile(self, perc):
        if len(self.flat_list) > 0:
            return int(np.percentile(np.array(self.flat_list), perc))
        else:
            return 0

    def length(self):
        return len(self.sliding_window)

    def print_stats(self):
        self.update_stats()
        if len(self.flat_list) > 10:
            output = "[" + str(self.statistics_type) + ","
            output += "mean:" + str(self.mean) + ","
            output += "min:" + str(self.get_min()) + ","
            output += "10th:" + str(self.get_percentile(10)) + ","
            output += "25th:" + str(self.get_percentile(25)) + ","
            output += "50th:" + str(self.get_percentile(50)) + ","
            output += "75th:" + str(self.get_percentile(75)) + ","
            output += "90th:" + str(self.get_percentile(90)) + ","
            output += "max:" + str(self.get_max()) + ","
            output += "vol:" + str(len(self.flat_list))
            output += "]"
        else:
            output = "[" + str(self.statistics_type) + ", more data needed]"

        print(output)


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
                return {'COCONUTS': -5, 'PINA_COLADAS': 5}