from flask import Flask, request
from gridbot import Gridbot
from threading import Thread

app = Flask(__name__)

@app.route("/create", methods=["POST"])
def create():
    # bot = Gridbot(NUM_GRID_LINES=8, CEIL_PRICE=1460, FLOOR_PRICE=1380, SYMBOL="ETH/USDT", POSITION_SIZE=0.001)
    try:
        bot = Gridbot(NUM_GRID_LINES = int(request.form["NUM_GRID_LINES"]),\
        CEIL_PRICE=float(request.form["CEIL_PRICE"]), FLOOR_PRICE=float(request.form["FLOOR_PRICE"]), \
        SYMBOL=request.form["SYMBOL"], POSITION_SIZE=float(request.form["POSITION_SIZE"]), INIT_BUY_FLAG=int(request.form["INIT_BUY_FLAG"]))
        bot.place_order()
    except Exception as e:
        return str(e)
    
    ## monitoring server
    # t = Thread(target=bot.monitor)
    # t.start()
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", threaded=True, debug=True)