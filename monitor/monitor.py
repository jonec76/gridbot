import db
import time, sys
from threading import Thread
import ccxt
import os

def get_active_accounts():
    res = db.load_table("task", col=["fk_discord_id"])
    accounts = []
    for r in res:
        accounts.append(r[0])
    accounts = set(accounts)
    return accounts

def get_exchange_table():
    table = {}
    accounts = get_active_accounts()
    for acc in accounts:
        res = db.load_table("user", col=["api_key", "secret_key"], condition=f"discord_id={acc}")
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
        # res = db.load_table("bot", col=["fk_discord_id", "symbol", "order", "fk_side_key", "grid_size", "position_size"])
        res = db.load_table("orders", col=["order_id", "fk_task_id"])
        time.sleep(check_order_freq)
        for r in res:
            order = r[0]
            task_id = r[1]
            task_res = db.load_table("task", col=["fk_discord_id", "symbol", "grid_size", "position_size"], condition=f"task_id={task_id}")
            task_res = task_res.fetchone()
            if task_res is None:
                continue
            discord_id = task_res[0]
            symbol = task_res[1]
            grid_size = task_res[2]
            position_size = task_res[3]

            exchange = exchange_table[discord_id]
            try:
                order_data = exchange.fetch_order(order)
            except Exception as e:
                print(f"{discord_id}: request failed, retrying")
                continue
                

            time.sleep(check_order_freq)
            order_info = order_data['info']
            if order_info['status'] == 'closed' and order_info['avgFillPrice'] is not None:
                old_order_id = order_info['id']
                closed_order_ids.append(old_order_id)
                try:
                    if order_info["side"] == "buy":
                        new_price = float(order_info['price']) + grid_size
                        new_side = "sell"
                    elif order_info["side"] == "sell":
                        new_price = float(order_info['price']) - grid_size
                        new_side = "buy"
                        db.increase_value("task", "profit_counter", 1, f"task_id='{task_id}'")
                    new_order_id = exchange.create_order(symbol, "limit", new_side, position_size, new_price)
                    print(new_order_id['info']['id'])
                    db.update_table("orders", [("fk_side_key", new_side), ("order_id", new_order_id['info']['id'])], f"order_id='{old_order_id}'")
                except Exception as e:
                    print(e)
                    continue
        # db.delete_orders(closed_order_ids)

if __name__ == '__main__':
    monitor_orders()
