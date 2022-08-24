# %%
from math import ceil
import ccxt, config, time, sys
from threading import Thread
import time
# import db
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
        initial_buy_status = self.exchange.fetch_order(initial_buy_order["id"])["status"].lower()
        
        if "canceled" in (initial_buy_status):
            raise Exception("Not enough balances at initial buying stage.")
    
    def place_order(self):
        try:
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
        except Exception as e:
            self.cancel_all_order()
            raise e

        # db.insert_orders(1, self.SYMBOL, {"sell": self.sell_orders, "buy": self.buy_orders}, self.grid_size, self.POSITION_SIZE)

    def cancel_all_order(self):
        for order in self.buy_orders + self.sell_orders:
            self.exchange.cancel_order(order["id"])

    
