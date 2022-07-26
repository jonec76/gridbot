# %%
from math import ceil
import ccxt, config, time, sys
from threading import Thread
import time

class FetchOrderThread(Thread):
    def __init__(self, exchange, id):
        Thread.__init__(self)
        self.exchange = exchange
        self.value = None
        self.id = id
 
    def run(self):
        print("checking order {}".format(self.id))
        try:
            order = self.exchange.fetch_order(self.id)
        except Exception as e:
            print("request failed, retrying")
        self.value = order

class Gridbot:
    def __init__(self, POSITION_SIZE=0, NUM_GRID_LINES=0, FLOOR_PRICE=0, CEIL_PRICE=0, SYMBOL="", API_KEY="", SECRET_KEY="", INIT_BUY_FLAG=False) -> None:
        self.buy_orders = []
        self.sell_orders = []

        self.check_order_freq = 1

        self.API_KEY = config.API_KEY
        self.SECRET_KEY = config.SECRET_KEY
        self.SYMBOL = SYMBOL
        self.POSITION_SIZE = POSITION_SIZE
        self.CEIL_PRICE = CEIL_PRICE
        self.FLOOR_PRICE = FLOOR_PRICE
        self.NUM_GRID_LINES = NUM_GRID_LINES
        self.grid_size = int((self.CEIL_PRICE - self.FLOOR_PRICE) // self.NUM_GRID_LINES)

        self.exchange = ccxt.ftx({
            'apiKey': self.API_KEY,
            'secret': self.SECRET_KEY
        })
        self.ticker = self.exchange.fetch_ticker(self.SYMBOL)
        if INIT_BUY_FLAG:
            self.init_buy()

    def init_buy(self):
        currency_price = float(self.ticker["info"]['price'])
        order_price = currency_price + self.grid_size
        sell_order_ctr = 0
        while order_price < self.CEIL_PRICE:
            sell_order_ctr += 1
            order_price += self.grid_size
        
        initial_buy_order = self.exchange.create_order(self.SYMBOL, "market", "buy", sell_order_ctr*self.POSITION_SIZE)
        print(f"Buy {sell_order_ctr*self.POSITION_SIZE} {self.SYMBOL} at {currency_price} usdt")
    
    def place_order(self):
        currency_price = float(self.ticker["info"]['price'])
        order_price = currency_price + self.grid_size
        while order_price < self.CEIL_PRICE:
            order = self.exchange.create_order(self.SYMBOL, "limit", "sell", self.POSITION_SIZE, order_price)
            self.sell_orders.append(order["info"])
            order_price += self.grid_size

        order_price = currency_price - self.grid_size
        while order_price > self.FLOOR_PRICE:
            order = self.exchange.create_order(self.SYMBOL, "limit", "buy", self.POSITION_SIZE, order_price)
            self.buy_orders.append(order["info"])
            order_price -= self.grid_size

    def monitor(self):
        while True:
            closed_order_ids = []
            thread_pool = []
            for order in self.buy_orders + self.sell_orders:
                tmp = FetchOrderThread(exchange=self.exchange, id=order['id'])
                tmp.start()
                time.sleep(self.check_order_freq)
                thread_pool.append(tmp)
            
            for tmp in thread_pool:
                tmp.join()
                data = tmp.value
                order_info = data['info']

                if order_info['status'] == 'closed':
                    closed_order_ids.append(order_info['id'])
                    if order_info["side"] == "buy":
                        new_sell_price = float(order_info['price']) + self.grid_size
                        new_order = self.exchange.create_order(self.SYMBOL, "limit", "sell", self.POSITION_SIZE, new_sell_price)
                        self.sell_orders.append(new_order)
                    
                    elif order_info["side"] == "sell":
                        new_buy_price = float(order_info['price']) - self.grid_size
                        new_order = self.exchange.create_order(self.SYMBOL, "limit", "buy", self.POSITION_SIZE, new_buy_price)
                        self.buy_orders.append(new_order)
            
            for order_id in closed_order_ids:
                self.buy_orders = [buy_order for buy_order in self.buy_orders if buy_order['id'] != order_id]
                self.sell_orders = [sell_order for sell_order in self.sell_orders if sell_order['id'] != order_id]

            if len(self.sell_orders) == 0:
                sys.exit("stopping bot, nothing left to sell")
