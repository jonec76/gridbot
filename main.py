from flask import Flask, jsonify
from gridbot import Gridbot
from threading import Thread

app = Flask(__name__)

@app.route("/create", methods=["POST"])
def create():
    g = Gridbot(NUM_GRID_LINES=8, CEIL_PRICE=1460, FLOOR_PRICE=1380, SYMBOL="ETH/USDT", POSITION_SIZE=0.001)
    g.place_order()
    t = Thread(target=g.monitor)
    t.start()
    return "ok!"

if __name__ == "__main__":
    app.run(threaded=True, debug=True)