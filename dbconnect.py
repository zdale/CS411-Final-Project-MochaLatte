import MySQLdb

def connection():
    conn = MySQLdb.connect(host="localhost",
                            user="root",
                            passwd="Gjx215321",
                            db = "cs411database")
    c = conn.cursor()

    return c,conn
