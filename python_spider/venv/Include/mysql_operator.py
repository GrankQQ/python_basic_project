import pymysql


def select(conn, sql):
    try:
        if conn is None:
            conn = pymysql.connect(host='39.106.63.165', user='root', passwd='!QAZ2wsx', db='refund')
        cur = conn.cursor()

        reCount = cur.execute(sql)
        print(reCount)
        data = cur.fetchall()

        cur.close()
        return data
    except Exception as e:
        print(e)
    finally:
        if conn is not None:
            conn.close()


def executeSql(conn, sql):
    try:
        if conn is None:
            conn = pymysql.connect(host='39.106.63.165', user='root', passwd='!QAZ2wsx', db='refund')
        cur = conn.cursor()

        reCount = cur.execute(sql)

        conn.commit()
        cur.close()
        return reCount
    except Exception as e:
        print(e)
    finally:
        if conn is not None:
            conn.close()

