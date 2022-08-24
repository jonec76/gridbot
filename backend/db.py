from asyncore import close_all
import mysql.connector

db = mysql.connector.connect(
  host="db",
  user="root",
  password="mysql",
  database="gridbot"
)

cursor = db.cursor(buffered=True)

def load_table(table_name, col=[], condition="1=1"):
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

table_side = {}
for row in load_table("table_side"):
    table_side[row[2]] = row[1]

def insert_orders(user, symbol, orders, grid_size, position_size):
    for side in orders:
        for order in orders[side]:
            key = table_side[side]
            sql = f"INSERT INTO bot (`symbol`, `order`, `fk_side_key`, `grid_size`, `position_size`, `fk_user_id`) VALUES ( '{symbol}', '{order['id']}', '{key}', {grid_size}, {position_size}, (SELECT id from user WHERE id={user}));"
            cursor.execute(sql)
            print(cursor)
            db.commit()

def delete_orders(order_ids):
    for id in order_ids:
        sql = f"DELETE FROM bot WHERE `order`='{id}';"
        cursor.execute(sql)
        db.commit()
