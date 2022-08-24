from turtle import position
from db import *
import time, sys
from threading import Thread
import ccxt

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
            raise e
        self.value = order


def get_active_accounts():
    res = load_table("bot", col=["fk_user_id"])
    accounts = []
    for r in res:
        accounts.append(r[0])
    accounts = set(accounts)
    return accounts

def get_exchange_table():
    table = {}
    accounts = get_active_accounts()
    for acc in accounts:
        res = load_table("user", col=["api_key", "secret_key"])
        for r in res:
            exchange = ccxt.ftx({
                'apiKey': r[0],
                'secret': r[1],
            })
            table[acc] = exchange
    return table

def get_active_orders():
    while True:
        thread_pool = []
        closed_order_ids = []
        check_order_freq = 1
        exchange_table = get_exchange_table()
        res = load_table("bot", col=["fk_user_id", "symbol", "order", "fk_side_key", "grid_size", "position_size"])
        for r in res:
            user_id = r[0]
            symbol = r[1]
            order = r[2]
            side = r[3]
            grid_size = r[4]
            position_size = r[5]
            print(order)

            exchange = exchange_table[user_id]
            try:
                order_data = exchange.fetch_order(order)
            except Exception as e:
                print("request failed, retrying")
                raise e

            time.sleep(check_order_freq)
            order_info = order_data['info']
            if order_info['status'] == 'closed':
                closed_order_ids.append(order_info['id'])
                try:
                    if order_info["side"] == "buy":
                        new_sell_price = float(order_info['price']) + grid_size
                        new_order = exchange.create_order(symbol, "limit", "sell", position_size, new_sell_price)
                        print(new_order)
                        insert_orders(1, symbol, {"sell": [new_order], "buy": []}, grid_size, position_size)
                    
                    elif order_info["side"] == "sell":
                        new_buy_price = float(order_info['price']) - grid_size
                        new_order = exchange.create_order(symbol, "limit", "buy", position_size, new_buy_price)
                        print(new_order)
                        insert_orders(1, symbol, {"sell": [], "buy": [new_order]}, grid_size, position_size)

                except Exception as e:
                    continue

        delete_orders(closed_order_ids)



get_active_orders()


# def monitor():
#     while True:
#         closed_order_ids = []
#         thread_pool = []
#         for order in self.buy_orders + self.sell_orders:
#             tmp = FetchOrderThread(exchange=self.exchange, id=order['id'])
#             tmp.start()
#             time.sleep(self.check_order_freq)
#             thread_pool.append(tmp)
        
#         for tmp in thread_pool:
#             tmp.join()
#             data = tmp.value
#             order_info = data['info']
#             if order_info['status'] == 'closed':
#                 closed_order_ids.append(order_info['id'])
#                 try:
#                     if order_info["side"] == "buy":
#                         new_sell_price = float(order_info['price']) + self.grid_size
#                         new_order = self.exchange.create_order(self.SYMBOL, "limit", "sell", self.POSITION_SIZE, new_sell_price)
#                         self.sell_orders.append(new_order)
#                         db.insert_orders(1, self.SYMBOL, {"sell": [new_order], "buy": []})
                    
#                     elif order_info["side"] == "sell":
#                         new_buy_price = float(order_info['price']) - self.grid_size
#                         new_order = self.exchange.create_order(self.SYMBOL, "limit", "buy", self.POSITION_SIZE, new_buy_price)
#                         self.buy_orders.append(new_order)
#                         db.insert_orders(1, self.SYMBOL, {"sell": [], "buy": [new_order]})

#                 except Exception as e:
#                     self.cancel_all_order()
#                     raise e

#         db.delete_orders(closed_order_ids)

#         for order_id in closed_order_ids:
#             self.buy_orders = [buy_order for buy_order in self.buy_orders if buy_order['id'] != order_id]
#             self.sell_orders = [sell_order for sell_order in self.sell_orders if sell_order['id'] != order_id]

#         if len(self.sell_orders) == 0:
#             sys.exit("stopping bot, nothing left to sell")