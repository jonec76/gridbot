import db
import time, sys
from threading import Thread
import ccxt
import os

def get_active_accounts():
    res = db.load_table("bot", col=["fk_discord_id"])
    accounts = []
    for r in res:
        accounts.append(r[0])
    accounts = set(accounts)
    return accounts

def get_exchange_table():
    table = {}
    accounts = get_active_accounts()
    for acc in accounts:
        res = db.load_table("user", col=["api_key", "secret_key"])
        for r in res:
            exchange = ccxt.ftx({
                'headers':{
                    'FTX-SUBACCOUNT': os.environ["SUB_ACCOUNT"]
                },
                'apiKey': r[0],
                'secret': r[1],
            })
            table[acc] = exchange
    return table

def monitor_orders():
    while True:
        closed_order_ids = []
        check_order_freq = 1
        exchange_table = get_exchange_table()
        res = db.load_table("bot", col=["fk_discord_id", "symbol", "order", "fk_side_key", "grid_size", "position_size"])
        time.sleep(check_order_freq)
        if res.fetchone() is None:
            print("None")
            continue
        for r in res:
            discord_id = r[0]
            symbol = r[1]
            order = r[2]
            side = r[3]
            grid_size = r[4]
            position_size = r[5]
            print(order)

            exchange = exchange_table[discord_id]
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
                        db.insert_orders(discord_id, symbol, {"sell": [new_order], "buy": []}, grid_size, position_size)
                    
                    elif order_info["side"] == "sell":
                        new_buy_price = float(order_info['price']) - grid_size
                        new_order = exchange.create_order(symbol, "limit", "buy", position_size, new_buy_price)
                        print(new_order)
                        db.insert_orders(discord_id, symbol, {"sell": [], "buy": [new_order]}, grid_size, position_size)

                except Exception as e:
                    print(e)
                    continue
        db.delete_orders(closed_order_ids)

if __name__ == '__main__':
    monitor_orders()