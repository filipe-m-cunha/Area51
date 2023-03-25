# CLOSE LONG
for bid_price in sorted(order_depth.buy_orders.keys(), reverse=True):
    bid_volume = min(order_depth.buy_orders[bid_price], num_long_positions)
    # if bid_price > np.mean(np.array(long_positions[:bid_volume])) \
    #     or np.mean(np.array(long_time[:bid_volume])) > 150 and can_long:
    if DECISION_CONDITIONS[product][0](bid_price, sliding_window_bid, sliding_window_ask, \
                                       long_positions, bid_volume, long_time) and CAN_LONG[product]:
        # can_short = False
        print(f"SELL {product} LONG", str(bid_volume) + "x", bid_price)
        orders.append(Order(product, bid_price, -bid_volume))
        num_long_positions -= bid_volume
        long_positions = long_positions[bid_volume:]
        long_time = long_time[bid_volume:]

# OPEN SHORT
for bid_price in sorted(order_depth.buy_orders.keys()):
    bid_volume = min(order_depth.buy_orders[bid_price], POSITION_LIMITS[product] - num_short_positions)
    # if bid_price > sliding_window_ask.get_percentile(10) - 2 and len(
    #         sliding_window_ask.sliding_window) > 2 and can_short:
    if DECISION_CONDITIONS[product][1](bid_price, sliding_window_bid, sliding_window_ask, \
                                       short_time, bid_volume, short_time) and CAN_SHORT[product]:
        print(f"SELL {product} SHORT", str(bid_volume) + "x", bid_price)
        orders.append(Order(product, bid_price, -bid_volume))
        num_short_positions += abs(bid_volume)
        short_positions += [bid_price for x in range(abs(bid_volume))]