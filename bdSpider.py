import time
import pymysql
import json
import datetime,calendar

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import smtplib
from email.mime.text import MIMEText
from email.header import Header




def spiderMain(city):
    db = pymysql.connect(host='localhost', user='root', password='zcr19960116', database='databases', port=3306)
    cursor = db.cursor()
    cursor.execute("select * from bytedance where create_date = '%s'" % datetime.date.today() + " and city_name = '%s'" % city )
    data = cursor.fetchone()
    if data is not None:
        print('今天已经存在数据,直接发邮件... ')
        # return
    print( ' 今天没有数据 开始爬数据... ')

    options = Options()
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    # 打开浏览器
    driver = webdriver.Chrome(options=options)

    def process_browser_log_entry(entry):
        response = json.loads(entry['message'])['message']
        return response

    url = ''
    if(city=='深圳'):
        url = 'https://jobs.bytedance.com/experienced/position?keywords=&category=6704215864629004552%2C6704215864591255820%2C6704215924712409352%2C6704216224387041544&location=CT_128&project=&type=&job_hot_flag=&current=1&limit=700&functionCategory=&tag='
    if(city=='上海'):
        url  = 'https://jobs.bytedance.com/experienced/position?keywords=&category=6704215864629004552%2C6704215864591255820%2C6704215924712409352%2C6704216224387041544&location=CT_125&project=&type=&job_hot_flag=&current=1&limit=700&functionCategory=&tag='
    driver.get(
        url
    )
    time.sleep(15)
    browser_log = driver.get_log('performance')

    events = [process_browser_log_entry(entry) for entry in browser_log]

    events = [event for event in events
              if 'Network.responseReceived' in event['method']
              and 'response' in event['params'].keys()
              and 'posts' in event['params']['response']['url']
              ]

    resp = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': events[0]['params']['requestId']})
    # print(resp)
    bodyjson = json.loads(resp['body'])

    for jobAttrs in bodyjson['data']['job_post_list']:
        uuid = jobAttrs['id']
        jobUrl = 'https://jobs.bytedance.com/experienced/position/' + uuid + '/detail'
        job_name = jobAttrs['title']
        description = jobAttrs['description']
        requirement = jobAttrs['requirement']
        # print(uuid + job_name + description + requirement)
        sql = f'insert into bytedance (`uuid`,`name`,`description`,url,job_attr,jd,create_date,city_name) values (%s,%s,%s,%s,%s,%s,%s,%s)'
        today = datetime.date.today()
        cursor.execute(sql, (uuid, job_name, description, jobUrl, "", requirement, today,city))

    db.commit()
    db.close()
    driver.quit()

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
        print(str(getYesterday_workday())+"的数据为空,把日期计为数据库中最大的日期;")
        cursor.execute("select max(create_date) from bytedance where 1=1 and create_date != '%s' " % datetime.date.today() +" and city_name = '%s'" % city_name )
        maxDate = cursor.fetchone()
        print(str(getYesterday_workday())+ "的数据为空,把日期计为数据库中最大的日期:" + maxDate[0])
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

def sendMail(datum,city_name):
    #设置服务器所需信息
    #163邮箱服务器地址
    mail_host = 'smtp.163.com'
    #163用户名
    mail_user = 'zcr20090431@163.com'
    #密码(部分邮箱为授权码)
    mail_pass = 'HFFZZLANXBRKFULI'
    #邮件发送方邮箱地址
    sender = 'zcr20090431@163.com'
    #邮件接受方邮箱地址，注意需要[]包裹，这意味着你可以写多个邮件地址群发
    receivers = ['739417226@qq.com','zcr20090430@163.com']


    mail_msg = """
    <p> 睿睿统计的 ❤️ 新增岗位详情</p>
    """


    for data in datum:
         subStr = ""
         jobHerf = data[8]
         jobName = data[2]
         subStr = subStr + '<p><a href=\"%s\">%s</a></p>'%(jobHerf,jobName)
         subStr+='<p><p>---job description---</p>'
         jobDes = data[3]
         for descri in jobDes.split('\n'):
             subStr+='<li>%s</li>'%(descri)
         subStr+='</p>'

         subStr += '<p><p>---job requirement---</p>'
         jobJd = data[4]
         for jd in jobJd.split('\n'):
             subStr += '<li>%s</li>' % (jd)
         subStr += '</p>'

         mail_msg = mail_msg + subStr
    message = MIMEText(mail_msg, 'html', 'utf-8')
    #邮件主题
    subject = '[有效]ByteDance 今日新增产品职位-'+ city_name
    message['Subject'] = Header(subject, 'utf-8')
    #发送方信息
    message['From'] = sender
    #接受方信息
    message['To'] = receivers[0]
    #登录并发送邮件
    try:
        smtpObj = smtplib.SMTP()
        #连接到服务器
        smtpObj.connect(mail_host,25)
        #登录到服务器
        smtpObj.login(mail_user,mail_pass)
        #发送
        smtpObj.sendmail(
            sender,receivers,message.as_string())
        #退出
        smtpObj.quit()
        print('success')
    except smtplib.SMTPException as e:
        print('error',e) #打印错误

x = 3
if(x==1):
    spiderMain('深圳')
    datum = getTodayNewDatum('深圳')
    if len(datum) != 0:
        print('今天新增数据不为空')
        sendMail(datum,'深圳')
    else:
        print('今天新增数据为空')
if(x==2):
    spiderMain('上海')
    datum = getTodayNewDatum('上海')
    if len(datum) != 0:
        print('今天新增数据不为空')
        sendMail(datum, '上海')
    else:
        print('今天新增数据为空')
if(x==3):
    spiderMain('深圳')
    datum = getTodayNewDatum('深圳')
    if len(datum) != 0:
        print('今天新增数据不为空')
        sendMail(datum, '深圳')
    else:
        print('今天新增数据为空')
    spiderMain('上海')
    datum = getTodayNewDatum('上海')
    if len(datum) != 0:
        print('今天新增数据不为空')
        sendMail(datum, '上海')
    else:
        print('今天新增数据为空')




