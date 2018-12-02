import MySQLdb

def connection():
    conn = MySQLdb.connect(host="localhost",
                            user="mochalatte_jiaxuan2",
                            passwd="asdZXC0,./",
                            db = "mochalatte_cs411database")
    c = conn.cursor()

    return c,conn
