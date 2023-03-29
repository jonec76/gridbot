from flask import Flask, request
from gridbot import Gridbot, cancel_order
from threading import Thread
import db
import threading

def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t

app = Flask(__name__)

@app.route("/create", methods=["POST"])
def create():
    # bot = Gridbot(num_grid_lines=8, ceil_price=1460, floor_price=1380, symbol="ETH/USDT", position_size=0.001)
    # return {"result": True}
    try:
        bot = Gridbot(discord_id=request.form["discord_id"], num_grid_lines = int(request.form["num_grid_lines"]),\
        ceil_price=float(request.form["ceil_price"]), floor_price=float(request.form["floor_price"]), \
        symbol=request.form["symbol"], position_size=float(request.form["position_size"]), init_buy_flag=int(request.form["init_buy_flag"]))
        task_id = bot.place_order()
    except Exception as e:
        return {"result": False, "Error message": str(e)} 
    return {"result": True, "data": task_id}

@app.route("/isVerifiedUser", methods=["GET"])
def isVerifiedUser():
    discord_id = request.args.get('discord_id')
    res = db.load_table("user", condition=f"discord_id={discord_id}")
    if res.fetchone() is None:
        return {"result": False, "Error message": "Not a verified user"} 
    return {"result": True}

@app.route("/register", methods=["POST"])
def register():
    # rsa encryption/decryption
    try:
        db.insert_account(request.form["api_key"], request.form["secret_key"], request.form["discord_id"])
    except Exception as e:
        return {"result": False, "Error message": str(e)} 
    return {"result": True} 

@app.route("/getTasks", methods=["GET"])
def getTasks():
    discord_id = request.args.get('discord_id')
    res = db.load_table("task", condition=f"fk_discord_id={discord_id}")
    data = []
    for r in res:
        print(r)
        data.append({"task_id": r[1], "ceil_price": r[7], "floor_price": r[8], "symbol":r[3]})
    return {"result": True, "data": data} 

@app.route("/getKeys", methods=["GET"])
def getKeys():
    discord_id = request.args.get('discord_id')
    res = db.load_table("user", condition=f"discord_id={discord_id}")
    print(res)
    data = []
    for r in res:
        print(r)
        data.append({"api_key": r[1], "secret_key":r[2]})
    return {"result": True, "data": data} 

@app.route("/updateKey", methods=["POST"])
def updateKey():
    discord_id = request.form["discord_id"]
    db.update_table("user", [("api_key", request.form["api_key"]), ("secret_key", request.form["secret_key"])], condition=f"discord_id={discord_id}")
    return {"result": True} 

@app.route("/close", methods=["POST"])
def close():
    task_id = request.form["task_id"]
    try:
        cancel_order(task_id)
        db.delete_task(task_id)
    except Exception as e:
        return {"result": False, "Error message": str(e)} 
    return {"result": True} 

if __name__ == "__main__":
    set_interval(db.remain_connection, 2)
    app.run(host="0.0.0.0", threaded=True, debug=True)