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

SELL_GRID_SIZE = int((config.CEIL_PRICE - ticker['bid'])//config.NUM_SELL_GRID_LINES)
BUY_GRID_SIZE = int((ticker['bid'] - config.FLOOR_PRICE)//config.NUM_BUY_GRID_LINES)


order_price = int(ticker['bid']+SELL_GRID_SIZE)
while order_price < config.CEIL_PRICE:
    print("submitting market limit sell onrder at {}".format(order_price))
    order = exchange.create_order(config.SYMBOL, "limit", "sell", 0.001, order_price)
    sell_orders.append(order["info"])
    order_price += SELL_GRID_SIZE


order_price = int(ticker['bid']-BUY_GRID_SIZE)
while order_price > config.FLOOR_PRICE:
    print("submitting market limit buy onrder at {}".format(order_price))
    order = exchange.create_order(config.SYMBOL, "limit", "buy", 0.001, order_price)
    buy_orders.append(order["info"])
    order_price -= BUY_GRID_SIZE

# %%
import matplotlib.pyplot as plt
import matplotlib.transforms as transforms
from threading import Thread
import time
price = [float(ticker["info"]["price"])]*10

fig, ax=plt.subplots()
plt.gca().axes.get_yaxis().set_visible(False)
trans = transforms.blended_transform_factory(
    ax.get_yticklabels()[0].get_transform(), ax.transData)

plt.ylim(500, 2000)

class OrderThread(Thread):
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
    plt.cla()
    closed_order_ids = []
    try:
        ticker = exchange.fetch_ticker(config.SYMBOL)
    except Exception as e:
        print("request failed, retrying")
        continue
    
    
    price.append(float(ticker["info"]["price"]))
    ax.text(0, float(ticker["info"]["price"]), "{:.1f}".format(float(ticker["info"]["price"])), transform=trans, color="black", ha="right", va="center")

    price = price[1:]
    ax.plot(price)
    
    ## buy
    buy_thread_pool = []
    
    for buy_order in buy_orders:
        tmp_thread = OrderThread(buy_order['id'])
        tmp_thread.start()
        time.sleep(config.CHECK_ORDERS_FREQUENCY)
        buy_thread_pool.append(tmp_thread)
    
    for tmp in buy_thread_pool:
        tmp.join()
    
    for tmp in buy_thread_pool:
        data = tmp.value
        order_info = data['info']
        ax.axhline(y = float(order_info["price"]), color = 'green', linestyle = '--')
        ax.text(0,float(order_info["price"]), "{:.1f}".format(float(order_info["price"])), transform=trans, color="green", ha="right", va="center")

        if order_info['status'] == config.CLOSED_ORDER_STATUS:
            closed_order_ids.append(order_info['id'])
            print("buy order executed at {}".format(order_info['price']))
            new_sell_price = float(order_info['price']) + SELL_GRID_SIZE
            print("creating new limit sell order at {}".format(new_sell_price))
            new_order = exchange.create_order(config.SYMBOL, "limit", "sell", 0.001, new_sell_price)
            sell_orders.append(new_order)

    ## sell
    sell_thread_pool = []
    
    for sell_order in sell_orders:
        tmp_thread = OrderThread(sell_order['id'])
        tmp_thread.start()
        time.sleep(config.CHECK_ORDERS_FREQUENCY)
        sell_thread_pool.append(tmp_thread)
    
    for tmp in sell_thread_pool:
        tmp.join()
    
    for tmp in sell_thread_pool:
        data = tmp.value
        order_info = data['info']
        ax.axhline(y = float(order_info["price"]), color = 'r', linestyle = '--')
        ax.text(0,float(order_info["price"]), "{:.1f}".format(float(order_info["price"])), transform=trans, color="red", ha="right", va="center")

        if order_info['status'] == config.CLOSED_ORDER_STATUS:
            closed_order_ids.append(order_info['id'])
            print("sell order executed at {}".format(order_info['price']))
            new_buy_price = float(order_info['price']) - BUY_GRID_SIZE
            print("creating new limit buy order at {}".format(new_buy_price))
            new_order = exchange.create_order(config.SYMBOL, "limit", "buy", 0.001, new_buy_price)
            buy_orders.append(new_order)
    
    for order_id in closed_order_ids:
        buy_orders = [buy_order for buy_order in buy_orders if buy_order['id'] != order_id]
        sell_orders = [sell_order for sell_order in sell_orders if sell_order['id'] != order_id]

    if len(sell_orders) == 0:
        sys.exit("stopping bot, nothing left to sell")

    plt.draw()
    plt.pause(0.01)
