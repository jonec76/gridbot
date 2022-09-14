# %%
from math import ceil
import ccxt, time, sys
from threading import Thread
import time
import sys, os
import db
from time import sleep


class Gridbot:
    def __init__(self, position_size=0, num_grid_lines=0, floor_price=0, ceil_price=0, symbol="", discord_id=-1, init_buy_flag=False) -> None:
        self.buy_orders = []
        self.sell_orders = []

        self.check_order_freq = 1
        self.discord_id = discord_id
        self.symbol = symbol
        self.position_size = position_size
        self.ceil_price = ceil_price
        self.floor_price = floor_price
        self.num_grid_lines = num_grid_lines
        self.grid_size = (self.ceil_price - self.floor_price) / self.num_grid_lines
        self.init_buy_flag = init_buy_flag
        self.set_exchange()
        

    def set_exchange(self):
        res = db.load_table("user", col=["api_key", "secret_key"], condition=f"`discord_id`={self.discord_id}")
        datas = list(res)[0]
        if len(datas) == 0:
            print("Can't find member")
            return
        self.exchange = ccxt.ftx({
            'headers':{
                'FTX-SUBACCOUNT': os.environ["SUB_ACCOUNT"]
            },
            'apiKey': datas[0],
            'secret': datas[1]
        })
        self.ticker = self.exchange.fetch_ticker(self.symbol)
        if self.init_buy_flag:
            self.init_buy()

    def init_buy(self):
        currency_price = float(self.ticker["info"]['price'])
        order_price = currency_price + self.grid_size
        sell_order_ctr = 0
        while order_price < self.ceil_price:
            sell_order_ctr += 1
            order_price += self.grid_size
        
        initial_buy_order = self.exchange.create_order(self.symbol, "market", "buy", sell_order_ctr*self.position_size)
        initial_buy_status = self.exchange.fetch_order(initial_buy_order["id"])["status"].lower()
        
        if "canceled" in (initial_buy_status):
            raise Exception("Not enough balances at initial buying stage.")
    
    def place_order(self):
        try:
            currency_price = float(self.ticker["info"]['price'])
            order_price = currency_price + self.grid_size
            while order_price < self.ceil_price:
                order = self.exchange.create_order(self.symbol, "limit", "sell", self.position_size, order_price)
                self.sell_orders.append(order["info"])
                order_price += self.grid_size
                sleep(0.5)

            order_price = currency_price - self.grid_size
            while order_price > self.floor_price:
                order = self.exchange.create_order(self.symbol, "limit", "buy", self.position_size, order_price)
                self.buy_orders.append(order["info"])
                order_price -= self.grid_size
                sleep(0.5)

        except Exception as e:
            self.cancel_all_order()
            raise e

        db.insert_orders(self.discord_id, self.symbol, {"sell": self.sell_orders, "buy": self.buy_orders}, self.grid_size, self.position_size)

    def cancel_all_order(self):
        for order in self.buy_orders + self.sell_orders:
            self.exchange.cancel_order(order["id"])



def cancel_order(discord_id, orders):
    res = db.load_table('user', col=["api_key", "secret_key"], condition=f"`discord_id`={discord_id}")
    res = res.fetchone()
    if res is not None:
        exchange = ccxt.ftx({
            'headers':{
                'FTX-SUBACCOUNT': os.environ["SUB_ACCOUNT"]
            },
            'apiKey': res[0],
            'secret': res[1]
        })
        for order_id in orders:
            try:
                exchange.cancel_order(order_id)
            except:
                print("failed to cancel order: "+str(order_id))
    else:
        return 
