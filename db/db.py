from asyncore import close_all
from math import ceil
import mysql.connector
from datetime import datetime
import json
with open('config.json', 'r') as f:
    config = json.load(f)

db = mysql.connector.connect(
  host=config["host"],
  user=config["user"],
  password=config["password"],
  database=config["database"],
  autocommit=True
)

ctr = 0
def load_table(table_name, col=[], condition="1=1"):
    cursor = db.cursor(buffered=True)
    col_str = ""
    if col != []:
        for idx, c in enumerate(col):
            col_str += f"`{c}`"
            if idx != len(col) - 1:
                col_str += ","
    else:
        col_str = "*"
    sql = f"SELECT {col_str} FROM {table_name} WHERE {condition};"
    cursor.execute(sql)
    
    return cursor

def update_table(table_name, key_value, condition):
    cursor = db.cursor(buffered=True)
    sql_key_value  = ""
    for idx, data in enumerate(key_value):
        if idx == 0:
            sql_key_value += (data[0] + "= '" + data[1] +"'")
        else:
            sql_key_value += "," + data[0] + "= '" + data[1] +"'"
    sql = f"UPDATE {table_name} SET {sql_key_value} WHERE {condition};"
    print(sql)
    cursor.execute(sql)
    db.commit()

def increase_value(table_name, column, value, condition):
    cursor = db.cursor(buffered=True)
    sql = f"UPDATE {table_name} SET {column} = {column} + {value} WHERE {condition};"
    print(sql)
    cursor.execute(sql)
    db.commit()

table_side = {}
for row in load_table("table_side"):
    table_side[row[2]] = row[1]

def insert_orders(discord_id, symbol, orders, grid_size, position_size, ceil_price, floor_price):
    cursor = db.cursor(buffered=True)
    now = datetime.now() # current date and time

    task_id = now.strftime("%Y%m%d%H%M%S")
    sql = f"INSERT INTO task (`task_id`, `symbol`, `grid_size`, `position_size`, `fk_discord_id`, `ceil_price`, `floor_price`) VALUES ( '{task_id}', '{symbol}', {grid_size}, {position_size}, {discord_id}, {ceil_price}, {floor_price});"
    cursor.execute(sql)
    db.commit()

    for side in orders:
        for order in orders[side]:
            key = table_side[side]
            sql = f"INSERT INTO orders (`fk_task_id`, `order_id`, `fk_side_key`) VALUES ('{task_id}', '{order['id']}', '{key}');"
            cursor.execute(sql)
            db.commit()
    return task_id

def delete_task(task_id):
    cursor = db.cursor(buffered=True)
    sql = f"DELETE FROM orders WHERE `fk_task_id`='{task_id}';"
    cursor.execute(sql)
    db.commit()
    sql = f"DELETE FROM task WHERE `task_id`='{task_id}';"
    cursor.execute(sql)
    db.commit()

def delete_orders(order_ids):
    cursor = db.cursor(buffered=True)
    for id in order_ids:
        sql = f"DELETE FROM orders WHERE `order_id`='{id}';"
        cursor.execute(sql)
        db.commit()

def insert_account(api_key, secret_key, discord_id):
    cursor = db.cursor(buffered=True)
    sql = f"INSERT INTO `user` (`discord_id`, `api_key`, `secret_key`) VALUES ('{discord_id}', '{api_key}', '{secret_key}');"
    cursor.execute(sql)
    db.commit()

def remain_connection():
    cursor = db.cursor(buffered=True)
    cursor.execute("select * from table_side;")
    db.commit()
    return cursor


