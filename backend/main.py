from flask import Flask, request
from gridbot import Gridbot
from threading import Thread
import db

app = Flask(__name__)

@app.route("/create", methods=["POST"])
def create():
    # bot = Gridbot(num_grid_lines=8, ceil_price=1460, floor_price=1380, symbol="ETH/USDT", position_size=0.001)
    try:
        bot = Gridbot(discord_id=request.form["discord_id"], num_grid_lines = int(request.form["num_grid_lines"]),\
        ceil_price=float(request.form["ceil_price"]), floor_price=float(request.form["floor_price"]), \
        symbol=request.form["symbol"], position_size=float(request.form["position_size"]), init_buy_flag=int(request.form["init_buy_flag"]))
        bot.place_order()
    except Exception as e:
        return str(e)
    return "ok"

@app.route("/isValidUser", methods=["GET"])
def isValidUser():
    discord_id = request.args.get('discord_id')
    res = db.load_table("user", condition=f"discord_id={discord_id}")
    if res.fetchone() is None:
        return "false"
    return "true"

@app.route("/register", methods=["POST"])
def register():
    # rsa encryption/decryption
    db.insert_account(request.form["api_key"], request.form["secret_key"], request.form["discord_id"])
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", threaded=True, debug=True)