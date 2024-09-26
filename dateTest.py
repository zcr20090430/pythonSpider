import datetime,calendar
import time
import pymysql
import json
import datetime,calendar


def getTodayNewDatum(city_name):
    db = pymysql.connect(host='localhost', user='root', password='zcr19960116', database='databases', port=3306)

    cursor = db.cursor()

    sql_today = "select * from bytedance where create_date = '%s'" % datetime.date.today() +" and city_name = '%s'" % city_name

    sql_yes = "select * from bytedance where create_date = '%s'" % getYesterday_workday() +" and city_name = '%s'" % city_name

    cursor.execute(sql_today)

    data_today = cursor.fetchall()

    cursor.execute(sql_yes)

    data_yes = cursor.fetchall()


    print("当天的数据量为:" + str(len(data_today)))
    print(str(getYesterday_workday()) + "当天的数据量为:"+ str(len(data_yes)))
    if len(data_yes) == 0:
        print(str(getYesterday_workday())+"的数据为空,把日期计为数据库中最大的日期:")
        cursor.execute("select max(create_date) from bytedance where 1=1")
        maxDate = cursor.fetchone()
        print("的数据为空,把日期计为数据库中最大的日期:" + maxDate[0])
        sql_yes = "select * from bytedance where create_date = '%s'" % maxDate[0] +" and city_name = '%s'" % city_name
        cursor.execute(sql_yes)
        data_yes = cursor.fetchall()

    list_yeskey = []
    for data_y in data_yes:
        list_yeskey.append(data_y[1] + data_y[2])

    ret = []
    for data_t in data_today:
        if (data_t[1] + data_t[2] not in list_yeskey):
            ret.append(data_t)
    return ret

def getYesterday_workday():
    today = datetime.date.today()
    if today.weekday() == calendar.MONDAY:
        oneday = datetime.timedelta(days=3)
    else:
        oneday = datetime.timedelta(days=1)
    yesterday = today - oneday
    return yesterday

print(getTodayNewDatum("深圳"))