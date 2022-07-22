# %%
from math import ceil
import ccxt, config, time, sys
exchange = ccxt.ftx({
    'apiKey': config.API_KEY,
    'secret': config.SECRET_KEY
})

ticker = exchange.fetch_ticker(config.SYMBOL)
buy_orders = []
sell_orders = []
# orderbook = exchange.fetch_order_book('ETH/USDT', limit=100)
# initial_buy_order = exchange.create_order(config.SYMBOL, "limit", "buy", 0.002, 1200)

grid_size = int((config.CEIL_PRICE - config.FLOOR_PRICE) // config.NUM_GRID_LINES)
currency_price = float(ticker["info"]['price'])

order_price = currency_price + grid_size
while order_price < config.CEIL_PRICE:
    order = exchange.create_order(config.SYMBOL, "limit", "sell", 0.001, order_price)
    sell_orders.append(order["info"])
    order_price += grid_size

order_price = currency_price - grid_size
while order_price > config.FLOOR_PRICE:
    order = exchange.create_order(config.SYMBOL, "limit", "buy", 0.001, order_price)
    buy_orders.append(order["info"])
    order_price -= grid_size


from threading import Thread
import time

class FetchOrderThread(Thread):
    def __init__(self, id):
        Thread.__init__(self)
        self.value = None
        self.id = id
 
    def run(self):
        print("checking order {}".format(self.id))
        try:
            order = exchange.fetch_order(self.id)
            print(order["info"]["side"])
        except Exception as e:
            print("request failed, retrying")
        self.value = order

while True:
    closed_order_ids = []
    thread_pool = []
    for order in buy_orders + sell_orders:
        tmp = FetchOrderThread(order['id'])
        tmp.start()
        time.sleep(config.CHECK_ORDERS_FREQUENCY)
        thread_pool.append(tmp)
    
    for tmp in thread_pool:
        tmp.join()
        data = tmp.value
        order_info = data['info']

        if order_info['status'] == config.CLOSED_ORDER_STATUS:
            closed_order_ids.append(order_info['id'])
            if order_info["side"] == "buy":
                new_sell_price = float(order_info['price']) + grid_size
                new_order = exchange.create_order(config.SYMBOL, "limit", "sell", 0.001, new_sell_price)
                sell_orders.append(new_order)
            
            elif order_info["side"] == "sell":
                new_buy_price = float(order_info['price']) - grid_size
                new_order = exchange.create_order(config.SYMBOL, "limit", "buy", 0.001, new_buy_price)
                buy_orders.append(new_order)
    
    for order_id in closed_order_ids:
        buy_orders = [buy_order for buy_order in buy_orders if buy_order['id'] != order_id]
        sell_orders = [sell_order for sell_order in sell_orders if sell_order['id'] != order_id]

    if len(sell_orders) == 0:
        sys.exit("stopping bot, nothing left to sell")