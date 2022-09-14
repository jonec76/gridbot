from flask import Flask, request
from gridbot import Gridbot, cancel_order
from threading import Thread
import db

app = Flask(__name__)

@app.route("/create", methods=["POST"])
def create():
    # bot = Gridbot(num_grid_lines=8, ceil_price=1460, floor_price=1380, symbol="ETH/USDT", position_size=0.001)
    discord_id = request.form["discord_id"]
    symbol = request.form["symbol"]
    res = db.load_table("bot", col=["id"], condition=f"fk_discord_id='{discord_id}' AND symbol='{symbol}'")
    if res.fetchone() is None:
        try:
            bot = Gridbot(discord_id=request.form["discord_id"], num_grid_lines = int(request.form["num_grid_lines"]),\
            ceil_price=float(request.form["ceil_price"]), floor_price=float(request.form["floor_price"]), \
            symbol=request.form["symbol"], position_size=float(request.form["position_size"]), init_buy_flag=int(request.form["init_buy_flag"]))
            bot.place_order()
        except Exception as e:
            return str(e)
        return "ok"
    else:
        return "existing bot"

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


@app.route("/close", methods=["POST"])
def close():
    # rsa encryption/decryption
    discord_id = request.form["discord_id"]
    symbol = request.form["symbol"]
    res = db.load_table('bot', col=["order"], condition=f"fk_discord_id='{discord_id}' AND symbol='{symbol}'")
    orders = [r[0] for r in res]
    if len(orders) == 0:
        return "empty"
    db.delete_orders(orders)
    cancel_order(discord_id, orders)
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", threaded=True, debug=True)