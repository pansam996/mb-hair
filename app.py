import configparser
import datetime
import pickle
import os.path
import os,tempfile
import psycopg2
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
from imgurpython import ImgurClient

app = Flask(__name__)
config = configparser.ConfigParser()
config.read("config.ini")

## imgur key
client_id = config['imgur']['Client_ID']
client_secret = config['imgur']['Client_Secret']
service_album_id = 'mTWZmzL' #剪髮項目相簿
works_album_id = 'K6ZS6Fj' #作品集相簿
access_token = config['imgur']['Access_Token']
refresh_token = config['imgur']['Refresh_Token']


## line bot setting
line_bot_api = LineBotApi(config['line_bot']['Channel_Access_Token'])
handler = WebhookHandler(config['line_bot']['Channel_Secret'])

# time format setting
ISOTIMEFORMAT = '%m-%d %H:%M'
slot_table = ['0900','0930','1000','1030','1100','1130','1200','1230',
'1300','1330','1400','1430','1500','1530','1600','1630','1700','1730',
'1800','1830','1900','1930','2000','2030','2100','2130','2200']
time_table = ['09:00','09:30','10:00','10:30','11:00','11:30','12:00','12:30',
'13:00','13:30','14:00','14:30','15:00','15:30','16:00','16:30','17:00','17:30',
'18:00','18:30','19:00','19:30','20:00','20:30','21:00','21:30','22:00']
week_day_dict = {
        0 : '一',
        1 : '二',
        2 : '三',
        3 : '四',
        4 : '五',
        5 : '六',
        6 : '日',
    }
business_day = []
date_list = []

def update_bussiness_day():
    # DB set
    DATABASE_URL = os.environ['DATABASE_URL']
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()

    sql = "select off_date from manager where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
    cursor.execute(sql)
    conn.commit()

    off_date = cursor.fetchone()[0]
    off_date_list = off_date.split()

    business_day.clear()
    date_list.clear()

    _ = 0
    while(len(business_day) < 7):
        date = (datetime.datetime.now()+datetime.timedelta(days=_)).strftime("%m-%d")
        weekday = (datetime.datetime.now()+datetime.timedelta(days=_)).weekday()

        if date in off_date_list:
            _ += 1
            continue
        if weekday == 6 :
            _ += 1
            continue
        else:
            _ += 1
        date_list.append(date)
        business_day.append(date+" ("+ week_day_dict[weekday] +")")


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@handler.add(PostbackEvent)
def reply_postback(event):
    update_bussiness_day()
    userID = event.source.user_id
    userName = line_bot_api.get_profile(event.source.user_id).display_name

    if event.postback.data == "最新消息":
        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        sql = "select * from news_table order by id DESC"
        cursor.execute(sql)
        conn.commit()
        result = cursor.fetchall()

        if not result:
            news_status = "目前沒有最新消息唷😖"

            line_bot_api.reply_message(event.reply_token, TextSendMessage(news_status))
            return 0

        else:
            content = {
            "type": "carousel",
            "contents": [
                ]
            }
            max_num = len(result)
            if max_num > 10:
                max_num = 10

            for i in range(max_num):
                style1 = {
                    "type": "bubble",
                    "size": "mega",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                            {
                                "type": "image",
                                "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                                "aspectMode": "cover",
                                "size": "full",
                                "aspectRatio": "50:100"
                            }
                            ],
                            "cornerRadius": "10px"
                        },
                        {
                            "type": "text",
                            "text": "最新消息",
                            "size": "lg",
                            "weight": "bold",
                            "offsetTop": "5px"
                        }
                        ],
                        "paddingAll": "10px"
                    }
                }

                style2 = {
                    "type": "bubble",
                    "size": "mega",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                            {
                                "type": "image",
                                "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                                "aspectMode": "cover",
                                "size": "full",
                                "aspectRatio": "100:100"
                            },
                            {
                                "type": "image",
                                "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                                "aspectMode": "cover",
                                "size": "full",
                                "aspectRatio": "100:100"
                            }
                            ],
                            "cornerRadius": "10px"
                        },
                        {
                            "type": "text",
                            "text": "最新消息",
                            "size": "lg",
                            "weight": "bold",
                            "offsetTop": "5px"
                        }
                        ],
                        "paddingAll": "10px"
                    }
                }

                if result[i][3] != "":
                    style2['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                    style2['body']['contents'][0]['contents'][1]['url'] = result[i][3]
                    # 字數過多時
                    # 92~104
                    if len(result[i][1]) > 91:
                        for j in range(2,9):
                            text_block = {
                                "type": "text",
                                "text": "最新消息",
                                "size": "lg",
                                "weight": "bold",
                                "offsetTop": "3px"
                            }
                            style2['body']['contents'].insert(j,text_block)
                        style2['body']['contents'][1]['text'] = result[i][1][:13]
                        style2['body']['contents'][2]['text'] = result[i][1][13:26]
                        style2['body']['contents'][3]['text'] = result[i][1][26:39]
                        style2['body']['contents'][4]['text'] = result[i][1][39:52]
                        style2['body']['contents'][5]['text'] = result[i][1][52:65]
                        style2['body']['contents'][6]['text'] = result[i][1][65:78]
                        style2['body']['contents'][7]['text'] = result[i][1][78:91]
                        style2['body']['contents'][8]['text'] = result[i][1][91:]

                    # 78~91
                    elif len(result[i][1]) > 78:
                        for j in range(2,8):
                            text_block = {
                                "type": "text",
                                "text": "最新消息",
                                "size": "lg",
                                "weight": "bold",
                                "offsetTop": "3px"
                            }
                            style2['body']['contents'].insert(j,text_block)
                        style2['body']['contents'][1]['text'] = result[i][1][:13]
                        style2['body']['contents'][2]['text'] = result[i][1][13:26]
                        style2['body']['contents'][3]['text'] = result[i][1][26:39]
                        style2['body']['contents'][4]['text'] = result[i][1][39:52]
                        style2['body']['contents'][5]['text'] = result[i][1][52:65]
                        style2['body']['contents'][6]['text'] = result[i][1][65:78]
                        style2['body']['contents'][7]['text'] = result[i][1][78:]
                    elif len(result[i][1]) > 65:
                        for j in range(2,7):
                            text_block = {
                                "type": "text",
                                "text": "最新消息",
                                "size": "lg",
                                "weight": "bold",
                                "offsetTop": "3px"
                            }
                            style2['body']['contents'].insert(j,text_block)
                        print(i)
                        style2['body']['contents'][1]['text'] = result[i][1][:13]
                        style2['body']['contents'][2]['text'] = result[i][1][13:26]
                        style2['body']['contents'][3]['text'] = result[i][1][26:39]
                        style2['body']['contents'][4]['text'] = result[i][1][39:52]
                        style2['body']['contents'][5]['text'] = result[i][1][52:65]
                        style2['body']['contents'][6]['text'] = result[i][1][65:]
                    elif len(result[i][1]) > 52:
                        for j in range(2,6):
                            text_block = {
                                "type": "text",
                                "text": "最新消息",
                                "size": "lg",
                                "weight": "bold",
                                "offsetTop": "3px"
                            }
                            style2['body']['contents'].insert(j,text_block)
                        style2['body']['contents'][1]['text'] = result[i][1][:13]
                        style2['body']['contents'][2]['text'] = result[i][1][13:26]
                        style2['body']['contents'][3]['text'] = result[i][1][26:39]
                        style2['body']['contents'][4]['text'] = result[i][1][39:52]
                        style2['body']['contents'][5]['text'] = result[i][1][52:]
                    elif len(result[i][1]) > 39:
                        for j in range(2,5):
                            text_block = {
                                "type": "text",
                                "text": "最新消息",
                                "size": "lg",
                                "weight": "bold",
                                "offsetTop": "3px"
                            }
                            style2['body']['contents'].insert(j,text_block)
                        style2['body']['contents'][1]['text'] = result[i][1][:13]
                        style2['body']['contents'][2]['text'] = result[i][1][13:26]
                        style2['body']['contents'][3]['text'] = result[i][1][26:39]
                        style2['body']['contents'][4]['text'] = result[i][1][39:]
                    elif len(result[i][1]) > 26:
                        for j in range(2,4):
                            text_block = {
                                "type": "text",
                                "text": "最新消息",
                                "size": "lg",
                                "weight": "bold",
                                "offsetTop": "3px"
                            }
                            style2['body']['contents'].insert(j,text_block)
                        style2['body']['contents'][1]['text'] = result[i][1][:13]
                        style2['body']['contents'][2]['text'] = result[i][1][13:26]
                        style2['body']['contents'][3]['text'] = result[i][1][26:]
                    elif len(result[i][1]) > 13:
                        for j in range(2,3):
                            text_block = {
                                "type": "text",
                                "text": "最新消息",
                                "size": "lg",
                                "weight": "bold",
                                "offsetTop": "3px"
                            }
                            style2['body']['contents'].insert(j,text_block)
                        style2['body']['contents'][1]['text'] = result[i][1][:13]
                        style2['body']['contents'][2]['text'] = result[i][1][13:]
                    else:
                        style2['body']['contents'][1]['text'] = result[i][1]

                    content['contents'].append(style2)

                else:
                    style1['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                    # 字數過多時
                    # 92~104
                    if len(result[i][1]) > 91:
                        for j in range(2,9):
                            text_block = {
                                "type": "text",
                                "text": "最新消息",
                                "size": "lg",
                                "weight": "bold",
                                "offsetTop": "3px"
                            }
                            style1['body']['contents'].insert(j,text_block)
                        style1['body']['contents'][1]['text'] = result[i][1][:13]
                        style1['body']['contents'][2]['text'] = result[i][1][13:26]
                        style1['body']['contents'][3]['text'] = result[i][1][26:39]
                        style1['body']['contents'][4]['text'] = result[i][1][39:52]
                        style1['body']['contents'][5]['text'] = result[i][1][52:65]
                        style1['body']['contents'][6]['text'] = result[i][1][65:78]
                        style1['body']['contents'][7]['text'] = result[i][1][78:91]
                        style1['body']['contents'][8]['text'] = result[i][1][91:]

                    # 78~91
                    elif len(result[i][1]) > 78:
                        for j in range(2,8):
                            text_block = {
                                "type": "text",
                                "text": "最新消息",
                                "size": "lg",
                                "weight": "bold",
                                "offsetTop": "3px"
                            }
                            style1['body']['contents'].insert(j,text_block)
                        style1['body']['contents'][1]['text'] = result[i][1][:13]
                        style1['body']['contents'][2]['text'] = result[i][1][13:26]
                        style1['body']['contents'][3]['text'] = result[i][1][26:39]
                        style1['body']['contents'][4]['text'] = result[i][1][39:52]
                        style1['body']['contents'][5]['text'] = result[i][1][52:65]
                        style1['body']['contents'][6]['text'] = result[i][1][65:78]
                        style1['body']['contents'][7]['text'] = result[i][1][78:]
                    elif len(result[i][1]) > 65:
                        for j in range(2,7):
                            text_block = {
                                "type": "text",
                                "text": "最新消息",
                                "size": "lg",
                                "weight": "bold",
                                "offsetTop": "3px"
                            }
                            style1['body']['contents'].insert(j,text_block)
                        print(i)
                        style1['body']['contents'][1]['text'] = result[i][1][:13]
                        style1['body']['contents'][2]['text'] = result[i][1][13:26]
                        style1['body']['contents'][3]['text'] = result[i][1][26:39]
                        style1['body']['contents'][4]['text'] = result[i][1][39:52]
                        style1['body']['contents'][5]['text'] = result[i][1][52:65]
                        style1['body']['contents'][6]['text'] = result[i][1][65:]
                    elif len(result[i][1]) > 52:
                        for j in range(2,6):
                            text_block = {
                                "type": "text",
                                "text": "最新消息",
                                "size": "lg",
                                "weight": "bold",
                                "offsetTop": "3px"
                            }
                            style1['body']['contents'].insert(j,text_block)
                        style1['body']['contents'][1]['text'] = result[i][1][:13]
                        style1['body']['contents'][2]['text'] = result[i][1][13:26]
                        style1['body']['contents'][3]['text'] = result[i][1][26:39]
                        style1['body']['contents'][4]['text'] = result[i][1][39:52]
                        style1['body']['contents'][5]['text'] = result[i][1][52:]
                    elif len(result[i][1]) > 39:
                        for j in range(2,5):
                            text_block = {
                                "type": "text",
                                "text": "最新消息",
                                "size": "lg",
                                "weight": "bold",
                                "offsetTop": "3px"
                            }
                            style1['body']['contents'].insert(j,text_block)
                        style1['body']['contents'][1]['text'] = result[i][1][:13]
                        style1['body']['contents'][2]['text'] = result[i][1][13:26]
                        style1['body']['contents'][3]['text'] = result[i][1][26:39]
                        style1['body']['contents'][4]['text'] = result[i][1][39:]
                    elif len(result[i][1]) > 26:
                        for j in range(2,4):
                            text_block = {
                                "type": "text",
                                "text": "最新消息",
                                "size": "lg",
                                "weight": "bold",
                                "offsetTop": "3px"
                            }
                            style1['body']['contents'].insert(j,text_block)
                        style1['body']['contents'][1]['text'] = result[i][1][:13]
                        style1['body']['contents'][2]['text'] = result[i][1][13:26]
                        style1['body']['contents'][3]['text'] = result[i][1][26:]
                    elif len(result[i][1]) > 13:
                        for j in range(2,3):
                            text_block = {
                                "type": "text",
                                "text": "最新消息",
                                "size": "lg",
                                "weight": "bold",
                                "offsetTop": "3px"
                            }
                            style1['body']['contents'].insert(j,text_block)
                        style1['body']['contents'][1]['text'] = result[i][1][:13]
                        style1['body']['contents'][2]['text'] = result[i][1][13:]
                    else:
                        style1['body']['contents'][1]['text'] = result[i][1]

                    content['contents'].append(style1)

            line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="目前最新消息",contents=content))


            return 0

    if event.postback.data == "聯絡我們":
        contact_us_flex = {
            "type": "bubble",
            "size": "giga",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                    {
                        "type": "image",
                        "url": "https://imgur.com/1KGFakd.jpg",
                        "size": "5xl",
                        "aspectMode": "cover",
                        "aspectRatio": "150:196",
                        "gravity": "center",
                        "flex": 1
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://i.imgur.com/pOVQ6Ro.jpg",
                            "size": "full",
                            "aspectMode": "cover",
                            "aspectRatio": "150:98",
                            "gravity": "center"
                        },
                        {
                            "type": "image",
                            "url": "https://i.imgur.com/5BiqNjh.jpg",
                            "size": "full",
                            "aspectMode": "cover",
                            "aspectRatio": "150:98",
                            "gravity": "center"
                        }
                        ],
                        "flex": 1
                    }
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full"
                        }
                        ],
                        "cornerRadius": "100px",
                        "width": "72px",
                        "height": "72px"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "text",
                            "contents": [
                            {
                                "type": "span",
                                "text": "MB 髮藝",
                                "weight": "bold",
                                "color": "#000000",
                                "size": "lg"
                            }
                            ],
                            "size": "sm"
                        },
                        {
                            "type": "separator",
                            "margin": "md"
                        },
                        {
                            "type": "text",
                            "contents": [
                            {
                                "type": "span",
                                "text": "設計師💇🏻‍♀️ 李貞",
                                "weight": "bold",
                                "color": "#000000"
                            }
                            ],
                            "size": "sm",
                            "margin": "md"
                        },
                        {
                            "type": "separator",
                            "margin": "md"
                        },
                        {
                            "type": "text",
                            "contents": [
                            {
                                "type": "span",
                                "text": "地址🏡 屏東市中華路431號",
                                "weight": "bold",
                                "color": "#000000"
                            }
                            ],
                            "size": "sm",
                            "margin": "md"
                        },
                        {
                            "type": "separator",
                            "margin": "md"
                        },
                        {
                            "type": "text",
                            "contents": [
                            {
                                "type": "span",
                                "text": "聯絡電話 📞 (08)-7366715",
                                "weight": "bold",
                                "color": "#000000"
                            }
                            ],
                            "size": "sm",
                            "margin": "md"
                        }
                        ]
                    }
                    ],
                    "spacing": "xl",
                    "paddingAll": "20px"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                    {
                        "type": "button",
                        "action": {
                        "type": "uri",
                        "label": "髮妝詢問",
                        "uri": "https://line.me/ti/p/MY9sqcvY6h"
                        },
                        "gravity": "center",
                        "height": "md",
                        "flex": 1
                    },
                    {
                        "type": "button",
                        "action": {
                        "type": "uri",
                        "label": "撥打電話",
                        "uri": "tel://087366715"
                        },
                        "height": "md",
                        "flex": 1,
                        "gravity": "center"
                    },
                    {
                        "type": "button",
                        "action": {
                        "type": "uri",
                        "label": "開啟導航",
                        "uri": "https://goo.gl/maps/UusBtgnWjZAMzYhW6"
                        },
                        "height": "md",
                        "flex": 1,
                        "gravity": "center"
                    }
                    ],
                    "paddingAll": "20px"
                },
                {
                    "type": "spacer"
                }
                ],
                "paddingAll": "0px"
            }
            }
        line_bot_api.reply_message(event.reply_token, FlexSendMessage(
                alt_text = '聯絡資訊',
                contents = contact_us_flex ))

        return 0

    if event.postback.data == "預約選項":
        #DB setting
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()


        # update DB to newest 7 dates
        theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
        today = str(theTime).split()[0]
        nowtime = str(theTime).split()[1]
        sql = "delete from reservation where reser_date < '" + today +"';"
        cursor.execute(sql)
        conn.commit()

        #DB update new customer into customer table
        query = f"""select * from customer where userid = (%s);"""
        cursor.execute(query,(userID,))
        conn.commit()
        if cursor.fetchone() == None:
            record = (userID,'',userName,'','','',0,'')
            table_columns = '(userid, service ,name,has_reser1,has_reser2,has_reser3,reser_num,reser_full_data)'
            postgres_insert_query = f"""INSERT INTO customer {table_columns} VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"""
            cursor.execute(postgres_insert_query, record)
            conn.commit()
        else:
            sql = "select reser_num from customer where userid = '" +userID + "';"
            cursor.execute(sql)
            conn.commit()

            reser_num = cursor.fetchone()[0]
            if reser_num == 3:
                line_bot_api.reply_message(event.reply_token, TextSendMessage("最多一次只能預約三個時段喔！😥\n如果要調整時段請到\"預約查詢做調整\""))
                return 0
        cursor.close()
        conn.close()


        line_bot_api.reply_message(event.reply_token, TextSendMessage(
            "請選擇美髮項目💇\n\n" +
            "剪髮： 30分鐘\n"   +
            "洗髮： 30分鐘 \n"   +
            "剪髮 + 洗髮： 1小時\n" +
            "護髮 + 洗髮： 1小時\n\n"  +
            "------------------\n\n" +
            "男生燙髮： 2小時 \n\n " +
            "女生燙髮： \n" +
            "短髮： 2小時\n" +
            "中長髮： 3.5小時\n" +
            "長髮： 4小時\n\n" +
            "------------------\n\n" +
            "男女染髮： \n" +
            "短髮： 1.5小時\n" +
            "中長髮： 2小時\n" +
            "長髮： 2.5小時"

            ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="剪髮"
                                            , data="剪髮")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="洗髮"
                                            , data="洗髮")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="剪髮+洗髮"
                                            , data="剪髮(洗髮)")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="護髮+護髮"
                                            , data="護髮(洗髮)")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="燙髮(男)"
                                            , data="燙髮(男)")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="燙髮(女)"
                                            , data="燙髮(女)")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="染髮"
                                            , data="染髮")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="染髮+剪髮"
                                            , data="染髮(剪髮)")
                    )
                ]
        )))
        return 0

    if event.postback.data == "預約查詢":
        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        #DB update new customer into customer table
        query = f"""select * from customer where userid = (%s);"""
        cursor.execute(query,(userID,))
        conn.commit()
        if cursor.fetchone() == None:
            record = (userID,'',userName,'','','',0,'')
            table_columns = '(userid, service ,name,has_reser1,has_reser2,has_reser3,reser_num,reser_full_data)'
            postgres_insert_query = f"""INSERT INTO customer {table_columns} VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"""
            cursor.execute(postgres_insert_query, record)
            conn.commit()

        sql = "select reser_num from customer where userid = '" +userID + "';"
        cursor.execute(sql)
        conn.commit()
        reser_num = int(cursor.fetchone()[0])
        if reser_num == 0:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("目前沒有預約紀錄唷💇"))
            return 0

        #取 has_reser_list
        has_reser_list = []
        for i in range(3):
            sql = "select has_reser"+ str(i+1) + " from customer where userid = '" + userID + "';"
            cursor.execute(sql)
            conn.commit()
            result = cursor.fetchone()[0]
            if result != '':
                has_reser_list.append(result)


        #檢查 has_reser日期 有沒有大於今天日期 若沒有 刪掉
        theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
        today = str(theTime).split()[0]
        nowtime = str(theTime).split()[1]

        re_write_into_has_reser = []
        for i in range(len(has_reser_list)):
            date = has_reser_list[i].split('#')[0].split()[0]
            time = has_reser_list[i].split('#')[1].split('-')[1]
            if today > date:
                reser_num-=1
                sql = "update customer set has_reser" + str(i+1) + " = '' where userid = '" + userID +"';"
                cursor.execute(sql)
                conn.commit()
                continue
            if today == date:
                if nowtime > time:
                    reser_num-=1
                    sql = "update customer set has_reser" + str(i+1) + " = '' where userid = '" + userID +"';"
                    cursor.execute(sql)
                    conn.commit()
                    continue
            re_write_into_has_reser.append(has_reser_list[i])


        #先清空 再 rewrite
        for i in range(3):
            sql = sql = "update customer set has_reser" + str(i+1) + " = '' where userid = '" + userID +"';"
            cursor.execute(sql)
            conn.commit()

        # rewrite into customer
        if reser_num > 0 :
            #rewrite data an update reser_num
            sql = "update customer set reser_num = " + str(reser_num) + " where userid = '" + userID +"';"
            cursor.execute(sql)
            conn.commit()

            for i in range(len(re_write_into_has_reser)):
                sql = "update customer set has_reser" + str(i+1) + " = '" + re_write_into_has_reser[i] + "' where userid = '" + userID +"';"
                cursor.execute(sql)
                conn.commit()
        # 沒有紀錄就 return 0
        else:
            sql = "update customer set reser_num = 0 where userid = '" + userID +"';"
            cursor.execute(sql)
            conn.commit()
            line_bot_api.reply_message(event.reply_token, TextSendMessage("目前沒有預約紀錄"))
            return 0



        search_reservation = {
            "type": "carousel",
            "contents": [
            ]
        }

        # 被 apprnd 的 item 必須在for 裡面初始化 ，否則append進去item 的都會參考同一個位置
        for i in range(len(re_write_into_has_reser)):
            research_data = {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "text",
                        "text": "預約紀錄",
                        "weight": "bold",
                        "color": "#1DB446",
                        "size": "xl",
                        "gravity": "center",
                        "align": "center"
                    },
                    {
                        "type": "separator",
                        "margin": "lg"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "xxl",
                        "spacing": "sm",
                        "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                            {
                                "type": "text",
                                "text": "預約日期",
                                "size": "lg",
                                "color": "#555555",
                                "flex": 0
                            },
                            {
                                "type": "text",
                                "text": "05-18 (三)",
                                "size": "lg",
                                "color": "#111111",
                                "align": "end"
                            }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                            {
                                "type": "text",
                                "text": "預約時間",
                                "size": "lg",
                                "color": "#555555",
                                "flex": 0
                            },
                            {
                                "type": "text",
                                "text": "14:00-15:00",
                                "size": "lg",
                                "color": "#111111",
                                "align": "end"
                            }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                            {
                                "type": "text",
                                "text": "美髮項目",
                                "size": "lg",
                                "color": "#555555",
                                "flex": 0
                            },
                            {
                                "type": "text",
                                "text": "燙髮",
                                "size": "lg",
                                "color": "#111111",
                                "align": "end"
                            }
                            ]
                        }
                        ]
                    },
                    {
                        "type": "button",
                        "action": {
                        "type": "postback",
                        "label": "刪除預約",
                        "data": "刪除預約"
                        },
                        "style": "primary",
                        "margin": "md"
                    }
                    ]
                }
            }
            search_reservation['contents'].append(research_data)


        for i in range(len(re_write_into_has_reser)):
            write_date = re_write_into_has_reser[i].split('#')[0]
            write_time = re_write_into_has_reser[i].split('#')[1]
            write_service = re_write_into_has_reser[i].split('#')[2]
            search_reservation['contents'][i]['body']['contents'][2]['contents'][0]['contents'][1]['text'] = write_date
            search_reservation['contents'][i]['body']['contents'][2]['contents'][1]['contents'][1]['text'] = write_time
            search_reservation['contents'][i]['body']['contents'][2]['contents'][2]['contents'][1]['text'] = write_service

            write_in_date = write_date.split()[0]
            write_in_time1_index = time_table.index(write_time.split('-')[0])
            write_in_time2_index = time_table.index(write_time.split('-')[1])

            write_in_data = str(write_in_date) + ' ' + str(write_in_time1_index) + ' ' + str(write_in_time2_index)
            search_reservation['contents'][i]['body']['contents'][3]['action']['data'] = '刪除預約 ' + write_in_data + ' ' + str(i+1)

        line_bot_api.reply_message(event.reply_token, FlexSendMessage(
                alt_text = '預約查詢結果',
                contents = search_reservation ))


        cursor.close()
        conn.close()

        return 0


    if event.postback.data == "作品集管理":
        line_bot_api.reply_message(event.reply_token, TextSendMessage("作品集管理"
            ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="新增作品"
                                            , data="新增作品")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="管理作品集"
                                            , data="管理作品集")
                    )
                ]
        )))
        return 0

    if event.postback.data == "查看作品集":
        line_bot_api.reply_message(event.reply_token, TextSendMessage("選擇『男生作品集』 or 『女生作品集』"
            ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="男生作品集"
                                            , data="查看男生作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="女生作品集"
                                            , data="查看女生作品集")
                    )
                ]
        )))

        return 0


    if event.postback.data == "查看男生作品集":
        line_bot_api.reply_message(event.reply_token, TextSendMessage("男生作品集"
            ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="剪髮作品集"
                                            , data="查看男生剪髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="染髮作品集"
                                            , data="查看男生染髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="燙髮作品集"
                                            , data="查看男生燙髮作品集")
                    )
                ]
        )))

        return 0

    if event.postback.data == "查看女生作品集":
        line_bot_api.reply_message(event.reply_token, TextSendMessage("女生作品集"
            ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="剪髮作品集"
                                            , data="查看女生剪髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="染髮作品集"
                                            , data="查看女生染髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="燙髮作品集"
                                            , data="查看女生燙髮作品集")
                    )
                ]
        )))

        return 0

    if event.postback.data == "上傳剪髮相簿":

        line_bot_api.reply_message(event.reply_token, TextSendMessage("分類至『男生』 or 『女生』"
            ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="男生"
                                            , data="男生剪髮")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="女生"
                                            , data="女生剪髮")
                    )
                ]
        )))

        return 0
    if event.postback.data == "上傳燙髮相簿":
        line_bot_api.reply_message(event.reply_token, TextSendMessage("分類至『男生』 or 『女生』"
            ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="男生"
                                            , data="男生燙髮")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="女生"
                                            , data="女生燙髮")
                    )
                ]
        )))

        return 0

    if event.postback.data == "上傳染髮相簿":
        line_bot_api.reply_message(event.reply_token, TextSendMessage("分類至『男生』 or 『女生』"
            ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="男生"
                                            , data="男生染髮")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="女生"
                                            , data="女生染髮")
                    )
                ]
        )))

        return 0


    if event.postback.data == "男生剪髮":
        line_bot_api.reply_message(event.reply_token, TextSendMessage("已新增至作品集。"))

        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        # get the url list
        sql = "select pic_1,pic_2,pic_3,pic_4 from manager where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()
        img_list = cursor.fetchone()

        # update to the portfolio
        table_columns = '(add_date,pic_1,pic_2,pic_3,pic_4)'
        sql = f"""insert into cut_man {table_columns} values (%s,%s,%s,%s,%s)"""
        date = (datetime.datetime.now()+datetime.timedelta(days=0)).strftime("%m-%d")
        cursor.execute(sql , (date,img_list[0],img_list[1],img_list[2],img_list[3]))
        conn.commit()

        #reset pic_num ,reset img_url
        sql = "update manager set status='',pic_num = '0' ,pic_1 = '', pic_2 = '', pic_3 = '' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()


        return 0

    if event.postback.data == "女生剪髮":
        line_bot_api.reply_message(event.reply_token, TextSendMessage("已新增至作品集。"))

        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        # get the url list
        sql = "select pic_1,pic_2,pic_3,pic_4 from manager where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()
        img_list = cursor.fetchone()

        # update to the portfolio
        table_columns = '(add_date,pic_1,pic_2,pic_3,pic_4)'
        sql = f"""insert into cut_male {table_columns} values (%s,%s,%s,%s,%s)"""
        date = (datetime.datetime.now()+datetime.timedelta(days=0)).strftime("%m-%d")
        cursor.execute(sql , (date,img_list[0],img_list[1],img_list[2],img_list[3]))
        conn.commit()

        #reset pic_num ,reset img_url
        sql = "update manager set status='',pic_num = '0' ,pic_1 = '', pic_2 = '', pic_3 = '' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()


        return 0

    if event.postback.data == "男生燙髮":
        line_bot_api.reply_message(event.reply_token, TextSendMessage("已新增至作品集。"))

        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        # get the url list
        sql = "select pic_1,pic_2,pic_3,pic_4 from manager where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()
        img_list = cursor.fetchone()

        # update to the portfolio
        table_columns = '(add_date,pic_1,pic_2,pic_3,pic_4)'
        sql = f"""insert into perm_man {table_columns} values (%s,%s,%s,%s,%s)"""
        date = (datetime.datetime.now()+datetime.timedelta(days=0)).strftime("%m-%d")
        cursor.execute(sql , (date,img_list[0],img_list[1],img_list[2],img_list[3]))
        conn.commit()

        #reset pic_num ,reset img_url
        sql = "update manager set status='',pic_num = '0' ,pic_1 = '', pic_2 = '', pic_3 = '' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()


        return 0

    if event.postback.data == "女生燙髮":
        line_bot_api.reply_message(event.reply_token, TextSendMessage("分類至『長髮』 or 『中長髮』 or 『短髮』"
            ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="長髮"
                                            , data="女生長燙髮")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="中長髮"
                                            , data="女生中長燙髮")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="短髮"
                                            , data="女生短燙髮")
                    )
                ]
        )))

        return 0

    if event.postback.data == "女生長燙髮":
        line_bot_api.reply_message(event.reply_token, TextSendMessage("已新增至作品集。"))

        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        # get the url list
        sql = "select pic_1,pic_2,pic_3,pic_4 from manager where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()
        img_list = cursor.fetchone()

        # update to the portfolio
        table_columns = '(add_date,pic_1,pic_2,pic_3,pic_4,lenth)'
        sql = f"""insert into perm_male {table_columns} values (%s,%s,%s,%s,%s,%s)"""
        date = (datetime.datetime.now()+datetime.timedelta(days=0)).strftime("%m-%d")
        cursor.execute(sql , (date,img_list[0],img_list[1],img_list[2],img_list[3],'l'))
        conn.commit()

        #reset pic_num ,reset img_url
        sql = "update manager set status='',pic_num = '0' ,pic_1 = '', pic_2 = '', pic_3 = '' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()


        return 0

    if event.postback.data == "女生中長燙髮":
        line_bot_api.reply_message(event.reply_token, TextSendMessage("已新增至作品集。"))

        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        # get the url list
        sql = "select pic_1,pic_2,pic_3,pic_4 from manager where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()
        img_list = cursor.fetchone()

        # update to the portfolio
        table_columns = '(add_date,pic_1,pic_2,pic_3,pic_4,lenth)'
        sql = f"""insert into perm_male {table_columns} values (%s,%s,%s,%s,%s,%s)"""
        date = (datetime.datetime.now()+datetime.timedelta(days=0)).strftime("%m-%d")
        cursor.execute(sql , (date,img_list[0],img_list[1],img_list[2],img_list[3],'m'))
        conn.commit()

        #reset pic_num ,reset img_url
        sql = "update manager set status='',pic_num = '0' ,pic_1 = '', pic_2 = '', pic_3 = '' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()


        return 0

    if event.postback.data == "女生短燙髮":
        line_bot_api.reply_message(event.reply_token, TextSendMessage("已新增至作品集。"))

        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        # get the url list
        sql = "select pic_1,pic_2,pic_3,pic_4 from manager where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()
        img_list = cursor.fetchone()

        # update to the portfolio
        table_columns = '(add_date,pic_1,pic_2,pic_3,pic_4,lenth)'
        sql = f"""insert into perm_male {table_columns} values (%s,%s,%s,%s,%s,%s)"""
        date = (datetime.datetime.now()+datetime.timedelta(days=0)).strftime("%m-%d")
        cursor.execute(sql , (date,img_list[0],img_list[1],img_list[2],img_list[3],'s'))
        conn.commit()

        #reset pic_num ,reset img_url
        sql = "update manager set status='',pic_num = '0' ,pic_1 = '', pic_2 = '', pic_3 = '' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()


        return 0

    if event.postback.data == "男生染髮":
        line_bot_api.reply_message(event.reply_token, TextSendMessage("已新增至作品集。"))

        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        # get the url list
        sql = "select pic_1,pic_2,pic_3,pic_4 from manager where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()
        img_list = cursor.fetchone()

        # update to the portfolio
        table_columns = '(add_date,pic_1,pic_2,pic_3,pic_4)'
        sql = f"""insert into dye_man {table_columns} values (%s,%s,%s,%s,%s)"""
        date = (datetime.datetime.now()+datetime.timedelta(days=0)).strftime("%m-%d")
        cursor.execute(sql , (date,img_list[0],img_list[1],img_list[2],img_list[3]))
        conn.commit()

        #reset pic_num ,reset img_url
        sql = "update manager set status='',pic_num = '0' ,pic_1 = '', pic_2 = '', pic_3 = '' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()


        return 0

    if event.postback.data == "女生染髮":
        line_bot_api.reply_message(event.reply_token, TextSendMessage("已新增至作品集。"))

        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        # get the url list
        sql = "select pic_1,pic_2,pic_3,pic_4 from manager where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()
        img_list = cursor.fetchone()

        # update to the portfolio
        table_columns = '(add_date,pic_1,pic_2,pic_3,pic_4)'
        sql = f"""insert into dye_male {table_columns} values (%s,%s,%s,%s,%s)"""
        date = (datetime.datetime.now()+datetime.timedelta(days=0)).strftime("%m-%d")
        cursor.execute(sql , (date,img_list[0],img_list[1],img_list[2],img_list[3]))
        conn.commit()

        #reset pic_num ,reset img_url
        sql = "update manager set status='',pic_num = '0' ,pic_1 = '', pic_2 = '', pic_3 = '' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()


        return 0

    if event.postback.data == '選擇樣式一':
        line_bot_api.reply_message(event.reply_token, TextSendMessage('請上傳一張圖片'))
        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        # set manager stauts '上傳圖片'
        sql = "update manager set status = '上傳圖片#樣式一' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()


        return 0

    if event.postback.data == '選擇樣式二':
        line_bot_api.reply_message(event.reply_token, TextSendMessage('請依序上傳兩張圖片'))
        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        # set manager stauts '上傳圖片'
        sql = "update manager set status = '上傳圖片#樣式二' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()


        return 0

    if event.postback.data == '選擇樣式三':
        line_bot_api.reply_message(event.reply_token, TextSendMessage('請依序上傳三張圖片'))
        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        # set manager stauts '上傳圖片'
        sql = "update manager set status = '上傳圖片#樣式三' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()


        return 0

    if event.postback.data == "新增作品":

        test = {
            "type": "carousel",
            "contents": [
                {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "50:100"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "選擇樣式一",
                            "data": "選擇樣式一"
                            },
                            "style": "primary",
                            "height": "md",
                            "offsetBottom": "10px"
                        }
                        ],
                        "offsetTop": "10px",
                        "paddingAll": "10px"
                    }
                    ],
                    "paddingAll": "10px"
                }
                },
                {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "選擇樣式二",
                            "data": "選擇樣式二"
                            },
                            "style": "primary",
                            "height": "md",
                            "offsetBottom": "10px"
                        }
                        ],
                        "offsetTop": "10px",
                        "paddingAll": "10px"
                    }
                    ],
                    "paddingAll": "10px"
                }
                },
                {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full"
                        }
                        ],
                        "cornerRadius": "200px"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "選擇樣式三",
                            "data": "選擇樣式三"
                            },
                            "style": "primary",
                            "height": "md",
                            "offsetBottom": "10px"
                        }
                        ],
                        "offsetTop": "10px",
                        "paddingAll": "10px"
                    }
                    ],
                    "paddingAll": "10px"
                }
                }
            ]
        }

        line_bot_api.reply_message(event.reply_token , FlexSendMessage('請選擇擺放樣式', contents= test))


        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        #清空manager status
        sql = "update manager set pic_num = '0',pic_1 = '', pic_2 = '', pic_3 = '' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()

        return 0

    if event.postback.data == "管理作品集":
        line_bot_api.reply_message(event.reply_token, TextSendMessage("管理作品集"
            ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="男生作品集"
                                            , data="男生作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="女生作品集"
                                            , data="女生作品集")
                    )
                ]
        )))

        return 0

    if event.postback.data == "男生作品集":
        line_bot_api.reply_message(event.reply_token, TextSendMessage("男生作品集"
            ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="男生剪髮作品集"
                                            , data="男生剪髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="男生染髮作品集"
                                            , data="男生染髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="男生燙髮作品集"
                                            , data="男生燙髮作品集")
                    )
                ]
        )))

        return 0

    if event.postback.data == "女生作品集":
        line_bot_api.reply_message(event.reply_token, TextSendMessage("女生作品集"
            ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="女生剪髮作品集"
                                            , data="女生剪髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="女生染髮作品集"
                                            , data="女生染髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="女生燙髮作品集"
                                            , data="女生燙髮作品集")
                    )
                ]
        )))

        return 0

# host look up
    if event.postback.data == "男生剪髮作品集":
        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        sql = "select * from cut_man order by id DESC"
        cursor.execute(sql)
        conn.commit()

        result = cursor.fetchall()

        if not result:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("目前沒有作品"))
            return 0

        content = {
            "type": "carousel",
            "contents": [
            ]
        }

        max_num = len(result)
        if max_num > 10:
            max_num = 10

        for i in range(max_num):
            style1 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "50:100"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "刪除",
                            "data": "刪除作品集#cut_man#"
                            },
                            "style": "primary",
                            "height": "md",
                            "offsetBottom": "10px"
                        }
                        ],
                        "offsetTop": "10px",
                        "paddingAll": "10px"
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style2 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "刪除",
                            "data": "刪除作品集#cut_man#"
                            },
                            "style": "primary",
                            "height": "md",
                            "offsetBottom": "10px"
                        }
                        ],
                        "offsetTop": "10px",
                        "paddingAll": "10px"
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style3 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full"
                        }
                        ],
                        "cornerRadius": "200px"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "刪除",
                            "data": "刪除作品集#cut_man#"
                            },
                            "style": "primary",
                            "height": "md",
                            "offsetBottom": "10px"
                        }
                        ],
                        "offsetTop": "10px",
                        "paddingAll": "10px"
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            if result[i][4]!= "":
                style3['body']['contents'][2]['contents'][0]['action']['data'] += str(result[i][0])
                style3['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style3['body']['contents'][1]['contents'][0]['url'] = result[i][3]
                style3['body']['contents'][1]['contents'][1]['url'] = result[i][4]

                content['contents'].append(style3)
            elif result[i][3] != "":
                style2['body']['contents'][1]['contents'][0]['action']['data'] += str(result[i][0])
                style2['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style2['body']['contents'][0]['contents'][1]['url'] = result[i][3]

                content['contents'].append(style2)

            else:
                style1['body']['contents'][1]['contents'][0]['action']['data'] += str(result[i][0])
                style1['body']['contents'][0]['contents'][0]['url'] = result[i][2]

                content['contents'].append(style1)
        line_bot_api.reply_message(event.reply_token,FlexSendMessage(alt_text="男生剪髮作品集",contents=content
        ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="男生剪髮作品集"
                                            , data="男生剪髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="男生染髮作品集"
                                            , data="男生染髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="男生燙髮作品集"
                                            , data="男生燙髮作品集")
                    )
                ]
        )))

        return 0


    if event.postback.data == "男生染髮作品集":
        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        sql = "select * from dye_man order by id DESC"
        cursor.execute(sql)
        conn.commit()

        result = cursor.fetchall()

        if not result:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("目前沒有作品"))
            return 0

        content = {
            "type": "carousel",
            "contents": [
            ]
        }

        max_num = len(result)
        if max_num > 10:
            max_num = 10

        for i in range(max_num):
            style1 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "50:100"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "刪除",
                            "data": "刪除作品集#dye_man#"
                            },
                            "style": "primary",
                            "height": "md",
                            "offsetBottom": "10px"
                        }
                        ],
                        "offsetTop": "10px",
                        "paddingAll": "10px"
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style2 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "刪除",
                            "data": "刪除作品集#dye_man#"
                            },
                            "style": "primary",
                            "height": "md",
                            "offsetBottom": "10px"
                        }
                        ],
                        "offsetTop": "10px",
                        "paddingAll": "10px"
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style3 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full"
                        }
                        ],
                        "cornerRadius": "200px"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "刪除",
                            "data": "刪除作品集#dye_man#"
                            },
                            "style": "primary",
                            "height": "md",
                            "offsetBottom": "10px"
                        }
                        ],
                        "offsetTop": "10px",
                        "paddingAll": "10px"
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            if result[i][4]!= "":
                style3['body']['contents'][2]['contents'][0]['action']['data'] += str(result[i][0])
                style3['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style3['body']['contents'][1]['contents'][0]['url'] = result[i][3]
                style3['body']['contents'][1]['contents'][1]['url'] = result[i][4]

                content['contents'].append(style3)
            elif result[i][3] != "":
                style2['body']['contents'][1]['contents'][0]['action']['data'] += str(result[i][0])
                style2['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style2['body']['contents'][0]['contents'][1]['url'] = result[i][3]

                content['contents'].append(style2)

            else:
                style1['body']['contents'][1]['contents'][0]['action']['data'] += str(result[i][0])
                style1['body']['contents'][0]['contents'][0]['url'] = result[i][2]

                content['contents'].append(style1)

        line_bot_api.reply_message(event.reply_token,FlexSendMessage(alt_text="男生染髮作品集",contents=content
        ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="男生剪髮作品集"
                                            , data="男生剪髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="男生染髮作品集"
                                            , data="男生染髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="男生燙髮作品集"
                                            , data="男生燙髮作品集")
                    )
                ]
        )))

        return 0

    if event.postback.data == "男生燙髮作品集":
        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        sql = "select * from perm_man order by id DESC"
        cursor.execute(sql)
        conn.commit()

        result = cursor.fetchall()
        if not result:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("目前沒有作品"))
            return 0

        content = {
            "type": "carousel",
            "contents": [
            ]
        }

        max_num = len(result)
        if max_num > 10:
            max_num = 10

        for i in range(max_num):
            style1 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "50:100"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "刪除",
                            "data": "刪除作品集#perm_man#"
                            },
                            "style": "primary",
                            "height": "md",
                            "offsetBottom": "10px"
                        }
                        ],
                        "offsetTop": "10px",
                        "paddingAll": "10px"
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style2 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "刪除",
                            "data": "刪除作品集#perm_man#"
                            },
                            "style": "primary",
                            "height": "md",
                            "offsetBottom": "10px"
                        }
                        ],
                        "offsetTop": "10px",
                        "paddingAll": "10px"
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style3 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full"
                        }
                        ],
                        "cornerRadius": "200px"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "刪除",
                            "data": "刪除作品集#perm_man#"
                            },
                            "style": "primary",
                            "height": "md",
                            "offsetBottom": "10px"
                        }
                        ],
                        "offsetTop": "10px",
                        "paddingAll": "10px"
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            if result[i][4]!= "":
                style3['body']['contents'][2]['contents'][0]['action']['data'] += str(result[i][0])
                style3['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style3['body']['contents'][1]['contents'][0]['url'] = result[i][3]
                style3['body']['contents'][1]['contents'][1]['url'] = result[i][4]

                content['contents'].append(style3)
            elif result[i][3] != "":
                style2['body']['contents'][1]['contents'][0]['action']['data'] += str(result[i][0])
                style2['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style2['body']['contents'][0]['contents'][1]['url'] = result[i][3]

                content['contents'].append(style2)

            else:
                style1['body']['contents'][1]['contents'][0]['action']['data'] += str(result[i][0])
                style1['body']['contents'][0]['contents'][0]['url'] = result[i][2]

                content['contents'].append(style1)

        line_bot_api.reply_message(event.reply_token,FlexSendMessage(alt_text="男生燙髮作品集",contents=content
        ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="男生剪髮作品集"
                                            , data="男生剪髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="男生染髮作品集"
                                            , data="男生染髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="男生燙髮作品集"
                                            , data="男生燙髮作品集")
                    )
                ]
        )))

        return 0

    if event.postback.data == "女生剪髮作品集":
        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        sql = "select * from cut_male order by id DESC"
        cursor.execute(sql)
        conn.commit()

        result = cursor.fetchall()
        if not result:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("目前沒有作品"))
            return 0

        content = {
            "type": "carousel",
            "contents": [
            ]
        }

        max_num = len(result)
        if max_num > 10:
            max_num = 10

        for i in range(max_num):
            style1 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "50:100"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "刪除",
                            "data": "刪除作品集#cut_male#"
                            },
                            "style": "primary",
                            "height": "md",
                            "offsetBottom": "10px"
                        }
                        ],
                        "offsetTop": "10px",
                        "paddingAll": "10px"
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style2 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "刪除",
                            "data": "刪除作品集#cut_male#"
                            },
                            "style": "primary",
                            "height": "md",
                            "offsetBottom": "10px"
                        }
                        ],
                        "offsetTop": "10px",
                        "paddingAll": "10px"
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style3 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full"
                        }
                        ],
                        "cornerRadius": "200px"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "刪除",
                            "data": "刪除作品集#cut_male#"
                            },
                            "style": "primary",
                            "height": "md",
                            "offsetBottom": "10px"
                        }
                        ],
                        "offsetTop": "10px",
                        "paddingAll": "10px"
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            if result[i][4]!= "":
                style3['body']['contents'][2]['contents'][0]['action']['data'] += str(result[i][0])
                style3['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style3['body']['contents'][1]['contents'][0]['url'] = result[i][3]
                style3['body']['contents'][1]['contents'][1]['url'] = result[i][4]

                content['contents'].append(style3)
            elif result[i][3] != "":
                style2['body']['contents'][1]['contents'][0]['action']['data'] += str(result[i][0])
                style2['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style2['body']['contents'][0]['contents'][1]['url'] = result[i][3]

                content['contents'].append(style2)

            else:
                style1['body']['contents'][1]['contents'][0]['action']['data'] += str(result[i][0])
                style1['body']['contents'][0]['contents'][0]['url'] = result[i][2]

                content['contents'].append(style1)

        line_bot_api.reply_message(event.reply_token,FlexSendMessage(alt_text="女生剪髮作品集",contents=content
        ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="女生剪髮作品集"
                                            , data="女生剪髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="女生染髮作品集"
                                            , data="女生染髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="女生燙髮作品集"
                                            , data="女生燙髮作品集")
                    )
                ]
        )))

        return 0

    if event.postback.data == "女生染髮作品集":
        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        sql = "select * from dye_male order by id DESC"
        cursor.execute(sql)
        conn.commit()

        result = cursor.fetchall()
        if not result:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("目前沒有作品"))
            return 0

        content = {
            "type": "carousel",
            "contents": [
            ]
        }

        max_num = len(result)
        if max_num > 10:
            max_num = 10

        for i in range(max_num):
            style1 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "50:100"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "刪除",
                            "data": "刪除作品集#dye_male#"
                            },
                            "style": "primary",
                            "height": "md",
                            "offsetBottom": "10px"
                        }
                        ],
                        "offsetTop": "10px",
                        "paddingAll": "10px"
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style2 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "刪除",
                            "data": "刪除作品集#dye_male#"
                            },
                            "style": "primary",
                            "height": "md",
                            "offsetBottom": "10px"
                        }
                        ],
                        "offsetTop": "10px",
                        "paddingAll": "10px"
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style3 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full"
                        }
                        ],
                        "cornerRadius": "200px"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "刪除",
                            "data": "刪除作品集#dye_male#"
                            },
                            "style": "primary",
                            "height": "md",
                            "offsetBottom": "10px"
                        }
                        ],
                        "offsetTop": "10px",
                        "paddingAll": "10px"
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            if result[i][4]!= "":
                style3['body']['contents'][2]['contents'][0]['action']['data'] += str(result[i][0])
                style3['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style3['body']['contents'][1]['contents'][0]['url'] = result[i][3]
                style3['body']['contents'][1]['contents'][1]['url'] = result[i][4]

                content['contents'].append(style3)
            elif result[i][3] != "":
                style2['body']['contents'][1]['contents'][0]['action']['data'] += str(result[i][0])
                style2['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style2['body']['contents'][0]['contents'][1]['url'] = result[i][3]

                content['contents'].append(style2)

            else:
                style1['body']['contents'][1]['contents'][0]['action']['data'] += str(result[i][0])
                style1['body']['contents'][0]['contents'][0]['url'] = result[i][2]

                content['contents'].append(style1)

        line_bot_api.reply_message(event.reply_token,FlexSendMessage(alt_text="女生染髮作品集",contents=content
        ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="女生剪髮作品集"
                                            , data="女生剪髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="女生染髮作品集"
                                            , data="女生染髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="女生燙髮作品集"
                                            , data="女生燙髮作品集")
                    )
                ]
        )))

        return 0

    if event.postback.data == "女生燙髮作品集":
        line_bot_api.reply_message(event.reply_token, TextSendMessage("選擇『長髮』 or 『中長髮』 or 『短髮』"
            ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="長髮"
                                            , data="女生長燙髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="中長髮"
                                            , data="女生中長燙髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="短髮"
                                            , data="女生短燙髮作品集")
                    )
                ]
        )))

        return 0

    if event.postback.data == "女生長燙髮作品集":
        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        sql = "select * from perm_male where lenth = 'l' order by id DESC"
        cursor.execute(sql)
        conn.commit()

        result = cursor.fetchall()
        if not result:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("目前沒有作品"))
            return 0

        content = {
            "type": "carousel",
            "contents": [
            ]
        }

        max_num = len(result)
        if max_num > 10:
            max_num = 10

        for i in range(max_num):
            style1 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "50:100"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "刪除",
                            "data": "刪除作品集#perm_male#"
                            },
                            "style": "primary",
                            "height": "md",
                            "offsetBottom": "10px"
                        }
                        ],
                        "offsetTop": "10px",
                        "paddingAll": "10px"
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style2 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "刪除",
                            "data": "刪除作品集#perm_male#"
                            },
                            "style": "primary",
                            "height": "md",
                            "offsetBottom": "10px"
                        }
                        ],
                        "offsetTop": "10px",
                        "paddingAll": "10px"
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style3 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full"
                        }
                        ],
                        "cornerRadius": "200px"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "刪除",
                            "data": "刪除作品集#perm_male#"
                            },
                            "style": "primary",
                            "height": "md",
                            "offsetBottom": "10px"
                        }
                        ],
                        "offsetTop": "10px",
                        "paddingAll": "10px"
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            if result[i][4]!= "":
                style3['body']['contents'][2]['contents'][0]['action']['data'] += str(result[i][0])
                style3['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style3['body']['contents'][1]['contents'][0]['url'] = result[i][3]
                style3['body']['contents'][1]['contents'][1]['url'] = result[i][4]

                content['contents'].append(style3)
            elif result[i][3] != "":
                style2['body']['contents'][1]['contents'][0]['action']['data'] += str(result[i][0])
                style2['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style2['body']['contents'][0]['contents'][1]['url'] = result[i][3]

                content['contents'].append(style2)

            else:
                style1['body']['contents'][1]['contents'][0]['action']['data'] += str(result[i][0])
                style1['body']['contents'][0]['contents'][0]['url'] = result[i][2]

                content['contents'].append(style1)

        line_bot_api.reply_message(event.reply_token,FlexSendMessage(alt_text="女生燙髮作品集",contents=content
        ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="女生剪髮作品集"
                                            , data="女生剪髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="女生染髮作品集"
                                            , data="女生染髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="女生燙髮作品集"
                                            , data="女生燙髮作品集")
                    )
                ]
        )))

        return 0

    if event.postback.data == "女生中長燙髮作品集":
        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        sql = "select * from perm_male where lenth = 'm' order by id DESC"
        cursor.execute(sql)
        conn.commit()

        result = cursor.fetchall()
        if not result:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("目前沒有作品"))
            return 0

        content = {
            "type": "carousel",
            "contents": [
            ]
        }

        max_num = len(result)
        if max_num > 10:
            max_num = 10

        for i in range(max_num):
            style1 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "50:100"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "刪除",
                            "data": "刪除作品集#perm_male#"
                            },
                            "style": "primary",
                            "height": "md",
                            "offsetBottom": "10px"
                        }
                        ],
                        "offsetTop": "10px",
                        "paddingAll": "10px"
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style2 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "刪除",
                            "data": "刪除作品集#perm_male#"
                            },
                            "style": "primary",
                            "height": "md",
                            "offsetBottom": "10px"
                        }
                        ],
                        "offsetTop": "10px",
                        "paddingAll": "10px"
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style3 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full"
                        }
                        ],
                        "cornerRadius": "200px"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "刪除",
                            "data": "刪除作品集#perm_male#"
                            },
                            "style": "primary",
                            "height": "md",
                            "offsetBottom": "10px"
                        }
                        ],
                        "offsetTop": "10px",
                        "paddingAll": "10px"
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            if result[i][4]!= "":
                style3['body']['contents'][2]['contents'][0]['action']['data'] += str(result[i][0])
                style3['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style3['body']['contents'][1]['contents'][0]['url'] = result[i][3]
                style3['body']['contents'][1]['contents'][1]['url'] = result[i][4]

                content['contents'].append(style3)
            elif result[i][3] != "":
                style2['body']['contents'][1]['contents'][0]['action']['data'] += str(result[i][0])
                style2['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style2['body']['contents'][0]['contents'][1]['url'] = result[i][3]

                content['contents'].append(style2)

            else:
                style1['body']['contents'][1]['contents'][0]['action']['data'] += str(result[i][0])
                style1['body']['contents'][0]['contents'][0]['url'] = result[i][2]

                content['contents'].append(style1)

        line_bot_api.reply_message(event.reply_token,FlexSendMessage(alt_text="女生燙髮作品集",contents=content
        ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="女生剪髮作品集"
                                            , data="女生剪髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="女生染髮作品集"
                                            , data="女生染髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="女生燙髮作品集"
                                            , data="女生燙髮作品集")
                    )
                ]
        )))

        return 0

    if event.postback.data == "女生短燙髮作品集":
        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        sql = "select * from perm_male where lenth = 's' order by id DESC"
        cursor.execute(sql)
        conn.commit()

        result = cursor.fetchall()
        if not result:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("目前沒有作品"))
            return 0

        content = {
            "type": "carousel",
            "contents": [
            ]
        }

        max_num = len(result)
        if max_num > 10:
            max_num = 10

        for i in range(max_num):
            style1 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "50:100"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "刪除",
                            "data": "刪除作品集#perm_male#"
                            },
                            "style": "primary",
                            "height": "md",
                            "offsetBottom": "10px"
                        }
                        ],
                        "offsetTop": "10px",
                        "paddingAll": "10px"
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style2 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "刪除",
                            "data": "刪除作品集#perm_male#"
                            },
                            "style": "primary",
                            "height": "md",
                            "offsetBottom": "10px"
                        }
                        ],
                        "offsetTop": "10px",
                        "paddingAll": "10px"
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style3 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full"
                        }
                        ],
                        "cornerRadius": "200px"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "刪除",
                            "data": "刪除作品集#perm_male#"
                            },
                            "style": "primary",
                            "height": "md",
                            "offsetBottom": "10px"
                        }
                        ],
                        "offsetTop": "10px",
                        "paddingAll": "10px"
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            if result[i][4]!= "":
                style3['body']['contents'][2]['contents'][0]['action']['data'] += str(result[i][0])
                style3['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style3['body']['contents'][1]['contents'][0]['url'] = result[i][3]
                style3['body']['contents'][1]['contents'][1]['url'] = result[i][4]

                content['contents'].append(style3)
            elif result[i][3] != "":
                style2['body']['contents'][1]['contents'][0]['action']['data'] += str(result[i][0])
                style2['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style2['body']['contents'][0]['contents'][1]['url'] = result[i][3]

                content['contents'].append(style2)

            else:
                style1['body']['contents'][1]['contents'][0]['action']['data'] += str(result[i][0])
                style1['body']['contents'][0]['contents'][0]['url'] = result[i][2]

                content['contents'].append(style1)

        line_bot_api.reply_message(event.reply_token,FlexSendMessage(alt_text="女生燙髮作品集",contents=content
        ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="女生剪髮作品集"
                                            , data="女生剪髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="女生染髮作品集"
                                            , data="女生染髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="女生燙髮作品集"
                                            , data="女生燙髮作品集")
                    )
                ]
        )))

        return 0

# guest look up
    if event.postback.data == "查看男生剪髮作品集":
        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        sql = "select * from cut_man order by id DESC"
        cursor.execute(sql)
        conn.commit()

        result = cursor.fetchall()
        if not result:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("目前沒有作品"))
            return 0

        content = {
            "type": "carousel",
            "contents": [
            ]
        }

        max_num = len(result)
        if max_num > 10:
            max_num = 10

        for i in range(max_num):
            style1 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "50:100"
                        }
                        ]
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style2 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        }
                        ]
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style3 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full"
                        }
                        ],
                        "cornerRadius": "200px"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        }
                        ]
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            if result[i][4]!= "":
                style3['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style3['body']['contents'][1]['contents'][0]['url'] = result[i][3]
                style3['body']['contents'][1]['contents'][1]['url'] = result[i][4]

                content['contents'].append(style3)
            elif result[i][3] != "":
                style2['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style2['body']['contents'][0]['contents'][1]['url'] = result[i][3]

                content['contents'].append(style2)

            else:
                style1['body']['contents'][0]['contents'][0]['url'] = result[i][2]

                content['contents'].append(style1)

        line_bot_api.reply_message(event.reply_token,FlexSendMessage(alt_text="男生剪髮作品集",contents=content
        ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="男生剪髮作品集"
                                            , data="查看男生剪髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="男生染髮作品集"
                                            , data="查看男生染髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="男生燙髮作品集"
                                            , data="查看男生燙髮作品集")
                    )
                ]
        )))

        return 0


    if event.postback.data == "查看男生染髮作品集":
        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        sql = "select * from dye_man order by id DESC"
        cursor.execute(sql)
        conn.commit()

        result = cursor.fetchall()
        if not result:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("目前沒有作品"))
            return 0

        content = {
            "type": "carousel",
            "contents": [
            ]
        }

        max_num = len(result)
        if max_num > 10:
            max_num = 10

        for i in range(max_num):
            style1 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "50:100"
                        }
                        ]
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style2 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        }
                        ]
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style3 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full"
                        }
                        ],
                        "cornerRadius": "200px"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        }
                        ]
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            if result[i][4]!= "":
                style3['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style3['body']['contents'][1]['contents'][0]['url'] = result[i][3]
                style3['body']['contents'][1]['contents'][1]['url'] = result[i][4]

                content['contents'].append(style3)
            elif result[i][3] != "":
                style2['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style2['body']['contents'][0]['contents'][1]['url'] = result[i][3]

                content['contents'].append(style2)

            else:
                style1['body']['contents'][0]['contents'][0]['url'] = result[i][2]

                content['contents'].append(style1)

        line_bot_api.reply_message(event.reply_token,FlexSendMessage(alt_text="男生染髮作品集",contents=content
        ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="男生剪髮作品集"
                                            , data="查看男生剪髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="男生染髮作品集"
                                            , data="查看男生染髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="男生燙髮作品集"
                                            , data="查看男生燙髮作品集")
                    )
                ]
        )))

        return 0

    if event.postback.data == "查看男生燙髮作品集":
        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        sql = "select * from perm_man order by id DESC"
        cursor.execute(sql)
        conn.commit()

        result = cursor.fetchall()
        if not result:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("目前沒有作品"))
            return 0

        content = {
            "type": "carousel",
            "contents": [
            ]
        }

        max_num = len(result)
        if max_num > 10:
            max_num = 10

        for i in range(max_num):
            style1 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "50:100"
                        }
                        ]
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style2 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        }
                        ]
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style3 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full"
                        }
                        ],
                        "cornerRadius": "200px"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        }
                        ]
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            if result[i][4]!= "":
                style3['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style3['body']['contents'][1]['contents'][0]['url'] = result[i][3]
                style3['body']['contents'][1]['contents'][1]['url'] = result[i][4]

                content['contents'].append(style3)
            elif result[i][3] != "":
                style2['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style2['body']['contents'][0]['contents'][1]['url'] = result[i][3]

                content['contents'].append(style2)

            else:
                style1['body']['contents'][0]['contents'][0]['url'] = result[i][2]

                content['contents'].append(style1)

        line_bot_api.reply_message(event.reply_token,FlexSendMessage(alt_text="男生燙髮作品集",contents=content
        ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="男生剪髮作品集"
                                            , data="查看男生剪髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="男生染髮作品集"
                                            , data="查看男生染髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="男生燙髮作品集"
                                            , data="查看男生燙髮作品集")
                    )
                ]
        )))

        return 0

    if event.postback.data == "查看女生剪髮作品集":
        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        sql = "select * from cut_male order by id DESC"
        cursor.execute(sql)
        conn.commit()

        result = cursor.fetchall()
        if not result:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("目前沒有作品"))
            return 0

        content = {
            "type": "carousel",
            "contents": [
            ]
        }

        max_num = len(result)
        if max_num > 10:
            max_num = 10

        for i in range(max_num):
            style1 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "50:100"
                        }
                        ]
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style2 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        }
                        ]
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style3 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full"
                        }
                        ],
                        "cornerRadius": "200px"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        }
                        ]
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            if result[i][4]!= "":
                style3['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style3['body']['contents'][1]['contents'][0]['url'] = result[i][3]
                style3['body']['contents'][1]['contents'][1]['url'] = result[i][4]

                content['contents'].append(style3)
            elif result[i][3] != "":
                style2['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style2['body']['contents'][0]['contents'][1]['url'] = result[i][3]

                content['contents'].append(style2)

            else:
                style1['body']['contents'][0]['contents'][0]['url'] = result[i][2]

                content['contents'].append(style1)

        line_bot_api.reply_message(event.reply_token,FlexSendMessage(alt_text="女生剪髮作品集",contents=content
        ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="女生剪髮作品集"
                                            , data="查看女生剪髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="女生染髮作品集"
                                            , data="查看女生染髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="女生燙髮作品集"
                                            , data="查看女生燙髮作品集")
                    )
                ]
        )))

        return 0

    if event.postback.data == "查看女生染髮作品集":
        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        sql = "select * from dye_male order by id DESC"
        cursor.execute(sql)
        conn.commit()

        result = cursor.fetchall()
        if not result:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("目前沒有作品"))
            return 0

        content = {
            "type": "carousel",
            "contents": [
            ]
        }

        max_num = len(result)
        if max_num > 10:
            max_num = 10

        for i in range(max_num):
            style1 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "50:100"
                        }
                        ]
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style2 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        }
                        ]
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style3 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full"
                        }
                        ],
                        "cornerRadius": "200px"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        }
                        ]
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            if result[i][4]!= "":
                style3['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style3['body']['contents'][1]['contents'][0]['url'] = result[i][3]
                style3['body']['contents'][1]['contents'][1]['url'] = result[i][4]

                content['contents'].append(style3)
            elif result[i][3] != "":
                style2['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style2['body']['contents'][0]['contents'][1]['url'] = result[i][3]

                content['contents'].append(style2)

            else:
                style1['body']['contents'][0]['contents'][0]['url'] = result[i][2]

                content['contents'].append(style1)

        line_bot_api.reply_message(event.reply_token,FlexSendMessage(alt_text="女生染髮作品集",contents=content
        ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="女生剪髮作品集"
                                            , data="查看女生剪髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="女生染髮作品集"
                                            , data="查看女生染髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="女生燙髮作品集"
                                            , data="查看女生燙髮作品集")
                    )
                ]
        )))

        return 0

    if event.postback.data == "查看女生燙髮作品集":
        line_bot_api.reply_message(event.reply_token, TextSendMessage("選擇『長髮』 or 『中長髮』 or 『短髮』"
            ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="長髮"
                                            , data="查看女生長燙髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="中長髮"
                                            , data="查看女生中長燙髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="短髮"
                                            , data="查看女生短燙髮作品集")
                    )
                ]
        )))

        return 0

    if event.postback.data == "查看女生長燙髮作品集":
        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        sql = "select * from perm_male where lenth = 'l' order by id DESC"
        cursor.execute(sql)
        conn.commit()

        result = cursor.fetchall()
        if not result:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("目前沒有作品"))
            return 0

        content = {
            "type": "carousel",
            "contents": [
            ]
        }

        max_num = len(result)
        if max_num > 10:
            max_num = 10

        for i in range(max_num):
            style1 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "50:100"
                        }
                        ]
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style2 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        }
                        ]
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style3 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full"
                        }
                        ],
                        "cornerRadius": "200px"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        }
                        ]
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            if result[i][4]!= "":
                style3['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style3['body']['contents'][1]['contents'][0]['url'] = result[i][3]
                style3['body']['contents'][1]['contents'][1]['url'] = result[i][4]

                content['contents'].append(style3)
            elif result[i][3] != "":
                style2['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style2['body']['contents'][0]['contents'][1]['url'] = result[i][3]

                content['contents'].append(style2)

            else:
                style1['body']['contents'][0]['contents'][0]['url'] = result[i][2]

                content['contents'].append(style1)

        line_bot_api.reply_message(event.reply_token,FlexSendMessage(alt_text="女生燙髮作品集",contents=content
        ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="女生剪髮作品集"
                                            , data="查看女生剪髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="女生染髮作品集"
                                            , data="查看女生染髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="女生燙髮作品集"
                                            , data="查看女生燙髮作品集")
                    )
                ]
        )))

        return 0

    if event.postback.data == "查看女生中長燙髮作品集":
        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        sql = "select * from perm_male where lenth = 'm' order by id DESC"
        cursor.execute(sql)
        conn.commit()

        result = cursor.fetchall()
        if not result:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("目前沒有作品"))
            return 0

        content = {
            "type": "carousel",
            "contents": [
            ]
        }

        max_num = len(result)
        if max_num > 10:
            max_num = 10

        for i in range(max_num):
            style1 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "50:100"
                        }
                        ]
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style2 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        }
                        ]
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style3 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full"
                        }
                        ],
                        "cornerRadius": "200px"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        }
                        ]
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            if result[i][4]!= "":
                style3['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style3['body']['contents'][1]['contents'][0]['url'] = result[i][3]
                style3['body']['contents'][1]['contents'][1]['url'] = result[i][4]

                content['contents'].append(style3)
            elif result[i][3] != "":
                style2['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style2['body']['contents'][0]['contents'][1]['url'] = result[i][3]

                content['contents'].append(style2)

            else:
                style1['body']['contents'][0]['contents'][0]['url'] = result[i][2]

                content['contents'].append(style1)

        line_bot_api.reply_message(event.reply_token,FlexSendMessage(alt_text="女生燙髮作品集",contents=content
        ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="女生剪髮作品集"
                                            , data="查看女生剪髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="女生染髮作品集"
                                            , data="查看女生染髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="女生燙髮作品集"
                                            , data="查看女生燙髮作品集")
                    )
                ]
        )))

        return 0

    if event.postback.data == "查看女生短燙髮作品集":
        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        sql = "select * from perm_male where lenth = 's' order by id DESC"
        cursor.execute(sql)
        conn.commit()

        result = cursor.fetchall()
        if not result:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("目前沒有作品"))
            return 0

        content = {
            "type": "carousel",
            "contents": [
            ]
        }

        max_num = len(result)
        if max_num > 10:
            max_num = 10

        for i in range(max_num):
            style1 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "50:100"
                        }
                        ]
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style2 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full",
                            "aspectRatio": "100:100"
                        }
                        ]
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            style3 = {
                "type": "bubble",
                "size": "giga",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "full"
                        }
                        ],
                        "cornerRadius": "200px"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        },
                        {
                            "type": "image",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                            "aspectMode": "cover",
                            "size": "5xl",
                            "aspectRatio": "150:300"
                        }
                        ]
                    }
                    ],
                    "paddingAll": "10px"
                }
            }

            if result[i][4]!= "":
                style3['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style3['body']['contents'][1]['contents'][0]['url'] = result[i][3]
                style3['body']['contents'][1]['contents'][1]['url'] = result[i][4]

                content['contents'].append(style3)
            elif result[i][3] != "":
                style2['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                style2['body']['contents'][0]['contents'][1]['url'] = result[i][3]

                content['contents'].append(style2)

            else:
                style1['body']['contents'][0]['contents'][0]['url'] = result[i][2]

                content['contents'].append(style1)

        line_bot_api.reply_message(event.reply_token,FlexSendMessage(alt_text="女生燙髮作品集",contents=content
        ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="女生剪髮作品集"
                                            , data="查看女生剪髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="女生染髮作品集"
                                            , data="查看女生染髮作品集")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="女生燙髮作品集"
                                            , data="查看女生燙髮作品集")
                    )
                ]
        )))

        return 0

    if "刪除作品集" in event.postback.data :
        table = event.postback.data.split('#')[1]
        data_id = event.postback.data.split('#')[2]

        if table == 'news_table':
            line_bot_api.reply_message(event.reply_token , TextSendMessage('已刪除這則最新消息。'))
        else:
            line_bot_api.reply_message(event.reply_token , TextSendMessage('已刪除該作品。'))
        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        sql = "delete from " + table + " where id = '" + data_id + "'"
        cursor.execute(sql)
        conn.commit()

        return 0

    if event.postback.data == "營業時間管理":
        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        offday_status = ""
        offshop_status = ""

        sql = "select off_date from manager where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()
        offday_status = cursor.fetchone()[0]


        sql = "select off_hour from manager where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()
        offshop_status = cursor.fetchone()[0]

        if offshop_status != "":
            offshop_status = offshop_status.split(' ')[0] +" "+ offshop_status.split(' ')[1]

        print(offshop_status)

        line_bot_api.reply_message(event.reply_token, TextSendMessage("要設定『休息日』 還是 『今日下班時間』?\n"  +
                                "目前設定的休息日 : \n" + str(offday_status) + "\n" + "目前設定的下班時間 : \n" + offshop_status,
                                quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=DatetimePickerAction(label="設定休息日",
                                                                        data="設定休息日",
                                                                        mode="date")
                                        ),
                                        QuickReplyButton(
                                            action=DatetimePickerAction(label="設定今日下班時間",
                                                                        data="設定下班時間",
                                                                        mode="time",
                                                                        initial= "09:00",
                                                                        min = "09:00",
                                                                        max = "18:00" )
                                        ),
                                        QuickReplyButton(
                                            action=PostbackAction(label="取消休息日設定"
                                            , data="取消休息日設定")
                                        ),
                                        QuickReplyButton(
                                            action=PostbackAction(label="取消下班時間設定"
                                            , data="取消下班時間設定")
                                        )
                                    ]
                            )))


        return 0


    if event.postback.data == "設定最新消息(一張圖片)":
        line_bot_api.reply_message(event.reply_token, TextSendMessage("請先上傳一張圖片"))
        # set manager status
        #DB setting
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        #reset pic_num ,reset img_url
        sql = "update manager set status='',pic_num = '0' ,pic_1 = '', pic_2 = '', pic_3 = '' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()

        sql = "update manager set status = '上傳一張圖片' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()

        cursor.close()
        conn.close()

        return 0

    if event.postback.data == "設定最新消息(兩張圖片)":
        line_bot_api.reply_message(event.reply_token, TextSendMessage("請先上傳兩張圖片"))
        # set manager status
        #DB setting
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        #init
        #reset pic_num ,reset img_url
        sql = "update manager set status='',pic_num = '0' ,pic_1 = '', pic_2 = '', pic_3 = '' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()

        sql = "update manager set status = '上傳兩張圖片' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()

        cursor.close()
        conn.close()

    if event.postback.data == "最新消息管理":

        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        sql = "select * from news_table order by id DESC"
        cursor.execute(sql)
        conn.commit()
        result = cursor.fetchall()


        if not result:
            news_status = "目前沒有最新消息唷😖"

            line_bot_api.reply_message(event.reply_token, TextSendMessage(news_status
                ,quick_reply=QuickReply(
                    items=[
                        QuickReplyButton(
                            action=PostbackAction(label="設定最新消息(文字 + 一張圖片)"
                                                , data="設定最新消息(一張圖片)")
                        ),
                        QuickReplyButton(
                            action=PostbackAction(label="設定最新消息(文字 + 兩張圖片)"
                                                , data="設定最新消息(兩張圖片)")
                        )
                    ]
            )))
            return 0

        else:
            content = {
            "type": "carousel",
            "contents": [
                ]
            }
            max_num = len(result)
            if max_num > 10:
                max_num = 10

            for i in range(max_num):
                style1 = {
                    "type": "bubble",
                    "size": "mega",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                            {
                                "type": "image",
                                "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                                "aspectMode": "cover",
                                "size": "full",
                                "aspectRatio": "50:100"
                            }
                            ],
                            "cornerRadius": "10px"
                        },
                        {
                            "type": "text",
                            "text": "最新消息",
                            "size": "lg",
                            "weight": "bold",
                            "offsetTop": "5px"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                            {
                                "type": "button",
                                "action": {
                                "type": "postback",
                                "label": "刪除",
                                "data": "刪除作品集#news_table#"
                                },
                                "style": "primary",
                                "height": "md",
                                "offsetBottom": "10px"
                            }
                            ],
                            "offsetTop": "10px",
                            "paddingAll": "10px"
                        }
                        ],
                        "paddingAll": "10px"
                    }
                }

                style2 = {
                    "type": "bubble",
                    "size": "mega",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                            {
                                "type": "image",
                                "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                                "aspectMode": "cover",
                                "size": "full",
                                "aspectRatio": "100:100"
                            },
                            {
                                "type": "image",
                                "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                                "aspectMode": "cover",
                                "size": "full",
                                "aspectRatio": "100:100"
                            }
                            ],
                            "cornerRadius": "10px"
                        },
                        {
                            "type": "text",
                            "text": "最新消息",
                            "size": "lg",
                            "weight": "bold",
                            "offsetTop": "5px"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                            {
                                "type": "button",
                                "action": {
                                "type": "postback",
                                "label": "刪除",
                                "data": "刪除作品集#news_table#"
                                },
                                "style": "primary",
                                "height": "md",
                                "offsetBottom": "10px"
                            }
                            ],
                            "offsetTop": "10px",
                            "paddingAll": "10px"
                        }
                        ],
                        "paddingAll": "10px"
                    }
                }

                if result[i][3] != "":
                    style2['body']['contents'][2]['contents'][0]['action']['data'] += str(result[i][0])
                    style2['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                    style2['body']['contents'][0]['contents'][1]['url'] = result[i][3]

                    # 字數過多時
                    # 92~104
                    if len(result[i][1]) > 91:
                        for j in range(2,9):
                            text_block = {
                                "type": "text",
                                "text": "最新消息",
                                "size": "lg",
                                "weight": "bold",
                                "offsetTop": "3px"
                            }
                            style2['body']['contents'].insert(j,text_block)
                        style2['body']['contents'][1]['text'] = result[i][1][:13]
                        style2['body']['contents'][2]['text'] = result[i][1][13:26]
                        style2['body']['contents'][3]['text'] = result[i][1][26:39]
                        style2['body']['contents'][4]['text'] = result[i][1][39:52]
                        style2['body']['contents'][5]['text'] = result[i][1][52:65]
                        style2['body']['contents'][6]['text'] = result[i][1][65:78]
                        style2['body']['contents'][7]['text'] = result[i][1][78:91]
                        style2['body']['contents'][8]['text'] = result[i][1][91:]

                    # 78~91
                    elif len(result[i][1]) > 78:
                        for j in range(2,8):
                            text_block = {
                                "type": "text",
                                "text": "最新消息",
                                "size": "lg",
                                "weight": "bold",
                                "offsetTop": "3px"
                            }
                            style2['body']['contents'].insert(j,text_block)
                        style2['body']['contents'][1]['text'] = result[i][1][:13]
                        style2['body']['contents'][2]['text'] = result[i][1][13:26]
                        style2['body']['contents'][3]['text'] = result[i][1][26:39]
                        style2['body']['contents'][4]['text'] = result[i][1][39:52]
                        style2['body']['contents'][5]['text'] = result[i][1][52:65]
                        style2['body']['contents'][6]['text'] = result[i][1][65:78]
                        style2['body']['contents'][7]['text'] = result[i][1][78:]
                    elif len(result[i][1]) > 65:
                        for j in range(2,7):
                            text_block = {
                                "type": "text",
                                "text": "最新消息",
                                "size": "lg",
                                "weight": "bold",
                                "offsetTop": "3px"
                            }
                            style2['body']['contents'].insert(j,text_block)
                        print(i)
                        style2['body']['contents'][1]['text'] = result[i][1][:13]
                        style2['body']['contents'][2]['text'] = result[i][1][13:26]
                        style2['body']['contents'][3]['text'] = result[i][1][26:39]
                        style2['body']['contents'][4]['text'] = result[i][1][39:52]
                        style2['body']['contents'][5]['text'] = result[i][1][52:65]
                        style2['body']['contents'][6]['text'] = result[i][1][65:]
                    elif len(result[i][1]) > 52:
                        for j in range(2,6):
                            text_block = {
                                "type": "text",
                                "text": "最新消息",
                                "size": "lg",
                                "weight": "bold",
                                "offsetTop": "3px"
                            }
                            style2['body']['contents'].insert(j,text_block)
                        style2['body']['contents'][1]['text'] = result[i][1][:13]
                        style2['body']['contents'][2]['text'] = result[i][1][13:26]
                        style2['body']['contents'][3]['text'] = result[i][1][26:39]
                        style2['body']['contents'][4]['text'] = result[i][1][39:52]
                        style2['body']['contents'][5]['text'] = result[i][1][52:]
                    elif len(result[i][1]) > 39:
                        for j in range(2,5):
                            text_block = {
                                "type": "text",
                                "text": "最新消息",
                                "size": "lg",
                                "weight": "bold",
                                "offsetTop": "3px"
                            }
                            style2['body']['contents'].insert(j,text_block)
                        style2['body']['contents'][1]['text'] = result[i][1][:13]
                        style2['body']['contents'][2]['text'] = result[i][1][13:26]
                        style2['body']['contents'][3]['text'] = result[i][1][26:39]
                        style2['body']['contents'][4]['text'] = result[i][1][39:]
                    elif len(result[i][1]) > 26:
                        for j in range(2,4):
                            text_block = {
                                "type": "text",
                                "text": "最新消息",
                                "size": "lg",
                                "weight": "bold",
                                "offsetTop": "3px"
                            }
                            style2['body']['contents'].insert(j,text_block)
                        style2['body']['contents'][1]['text'] = result[i][1][:13]
                        style2['body']['contents'][2]['text'] = result[i][1][13:26]
                        style2['body']['contents'][3]['text'] = result[i][1][26:]
                    elif len(result[i][1]) > 13:
                        for j in range(2,3):
                            text_block = {
                                "type": "text",
                                "text": "最新消息",
                                "size": "lg",
                                "weight": "bold",
                                "offsetTop": "3px"
                            }
                            style2['body']['contents'].insert(j,text_block)
                        style2['body']['contents'][1]['text'] = result[i][1][:13]
                        style2['body']['contents'][2]['text'] = result[i][1][13:]
                    else:
                        style2['body']['contents'][1]['text'] = result[i][1]

                    content['contents'].append(style2)

                else:
                    style1['body']['contents'][2]['contents'][0]['action']['data'] += str(result[i][0])
                    style1['body']['contents'][0]['contents'][0]['url'] = result[i][2]
                    # 字數過多時
                    # 92~104
                    if len(result[i][1]) > 91:
                        for j in range(2,9):
                            text_block = {
                                "type": "text",
                                "text": "最新消息",
                                "size": "lg",
                                "weight": "bold",
                                "offsetTop": "3px"
                            }
                            style1['body']['contents'].insert(j,text_block)
                        style1['body']['contents'][1]['text'] = result[i][1][:13]
                        style1['body']['contents'][2]['text'] = result[i][1][13:26]
                        style1['body']['contents'][3]['text'] = result[i][1][26:39]
                        style1['body']['contents'][4]['text'] = result[i][1][39:52]
                        style1['body']['contents'][5]['text'] = result[i][1][52:65]
                        style1['body']['contents'][6]['text'] = result[i][1][65:78]
                        style1['body']['contents'][7]['text'] = result[i][1][78:91]
                        style1['body']['contents'][8]['text'] = result[i][1][91:]

                    # 78~91
                    elif len(result[i][1]) > 78:
                        for j in range(2,8):
                            text_block = {
                                "type": "text",
                                "text": "最新消息",
                                "size": "lg",
                                "weight": "bold",
                                "offsetTop": "3px"
                            }
                            style1['body']['contents'].insert(j,text_block)
                        style1['body']['contents'][1]['text'] = result[i][1][:13]
                        style1['body']['contents'][2]['text'] = result[i][1][13:26]
                        style1['body']['contents'][3]['text'] = result[i][1][26:39]
                        style1['body']['contents'][4]['text'] = result[i][1][39:52]
                        style1['body']['contents'][5]['text'] = result[i][1][52:65]
                        style1['body']['contents'][6]['text'] = result[i][1][65:78]
                        style1['body']['contents'][7]['text'] = result[i][1][78:]
                    elif len(result[i][1]) > 65:
                        for j in range(2,7):
                            text_block = {
                                "type": "text",
                                "text": "最新消息",
                                "size": "lg",
                                "weight": "bold",
                                "offsetTop": "3px"
                            }
                            style1['body']['contents'].insert(j,text_block)
                        print(i)
                        style1['body']['contents'][1]['text'] = result[i][1][:13]
                        style1['body']['contents'][2]['text'] = result[i][1][13:26]
                        style1['body']['contents'][3]['text'] = result[i][1][26:39]
                        style1['body']['contents'][4]['text'] = result[i][1][39:52]
                        style1['body']['contents'][5]['text'] = result[i][1][52:65]
                        style1['body']['contents'][6]['text'] = result[i][1][65:]
                    elif len(result[i][1]) > 52:
                        for j in range(2,6):
                            text_block = {
                                "type": "text",
                                "text": "最新消息",
                                "size": "lg",
                                "weight": "bold",
                                "offsetTop": "3px"
                            }
                            style1['body']['contents'].insert(j,text_block)
                        style1['body']['contents'][1]['text'] = result[i][1][:13]
                        style1['body']['contents'][2]['text'] = result[i][1][13:26]
                        style1['body']['contents'][3]['text'] = result[i][1][26:39]
                        style1['body']['contents'][4]['text'] = result[i][1][39:52]
                        style1['body']['contents'][5]['text'] = result[i][1][52:]
                    elif len(result[i][1]) > 39:
                        for j in range(2,5):
                            text_block = {
                                "type": "text",
                                "text": "最新消息",
                                "size": "lg",
                                "weight": "bold",
                                "offsetTop": "3px"
                            }
                            style1['body']['contents'].insert(j,text_block)
                        style1['body']['contents'][1]['text'] = result[i][1][:13]
                        style1['body']['contents'][2]['text'] = result[i][1][13:26]
                        style1['body']['contents'][3]['text'] = result[i][1][26:39]
                        style1['body']['contents'][4]['text'] = result[i][1][39:]
                    elif len(result[i][1]) > 26:
                        for j in range(2,4):
                            text_block = {
                                "type": "text",
                                "text": "最新消息",
                                "size": "lg",
                                "weight": "bold",
                                "offsetTop": "3px"
                            }
                            style1['body']['contents'].insert(j,text_block)
                        style1['body']['contents'][1]['text'] = result[i][1][:13]
                        style1['body']['contents'][2]['text'] = result[i][1][13:26]
                        style1['body']['contents'][3]['text'] = result[i][1][26:]
                    elif len(result[i][1]) > 13:
                        for j in range(2,3):
                            text_block = {
                                "type": "text",
                                "text": "最新消息",
                                "size": "lg",
                                "weight": "bold",
                                "offsetTop": "3px"
                            }
                            style1['body']['contents'].insert(j,text_block)
                        style1['body']['contents'][1]['text'] = result[i][1][:13]
                        style1['body']['contents'][2]['text'] = result[i][1][13:]
                    else:
                        style1['body']['contents'][1]['text'] = result[i][1]

                    content['contents'].append(style1)

            line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="目前最新消息",contents=content
                ,quick_reply=QuickReply(
                    items=[
                        QuickReplyButton(
                            action=PostbackAction(label="設定最新消息(文字 + 一張圖片)"
                                                , data="設定最新消息(一張圖片)")
                        ),
                        QuickReplyButton(
                            action=PostbackAction(label="設定最新消息(文字 + 兩張圖片)"
                                                , data="設定最新消息(兩張圖片)")
                        )
                    ]
            )))

            return 0
        return 0

    if "休息#" in event.postback.data:
        # DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        select_day = event.postback.data.split('#')[2]
        number = int(event.postback.data.split('#')[1])
        date_object = datetime.datetime.strptime(select_day, '%Y-%m-%d').date()
        rest_end = (date_object + datetime.timedelta(days=number)).strftime("%m-%d")
        rest_Day = ''
        for i in range(number+1):
            rest_day = (date_object + datetime.timedelta(days=i)).strftime("%m-%d")
            rest_Day += rest_day + " "

        line_bot_api.reply_message(event.reply_token, TextSendMessage("已設定 " + select_day[5:] + "~" + rest_end + "休息"))

        # write to manager off_date:
        sql = "update manager set off_date = '" + rest_Day + "' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()

        cursor.close()
        conn.close()
        return 0

    if "設定休息日" in  event.postback.data:
        select_day = str(event.postback.params['date'])
        select_day_without_year = select_day[5:]
        # str to dateobject
        date_object = datetime.datetime.strptime(select_day, '%Y-%m-%d').date()
        week_day = date_object.weekday()
        line_bot_api.reply_message(event.reply_token,TextSendMessage("請問要從 " + select_day_without_year + " (" +week_day_dict[week_day] + ") 休息到哪一天？"
                                ,quick_reply=QuickReply(
                                    items=[
                                    QuickReplyButton(
                                        action=PostbackAction(label= (date_object + datetime.timedelta(days=0)).strftime("%m-%d") + " (" + week_day_dict[week_day] + ")"
                                                            , data="休息#0#" + select_day)
                                    ),
                                    QuickReplyButton(
                                        action=PostbackAction(label=(date_object + datetime.timedelta(days=1)).strftime("%m-%d") + " (" + week_day_dict[(week_day + 1) % 7] + ")"
                                                            , data="休息#1#" + select_day)
                                    ),
                                    QuickReplyButton(
                                        action=PostbackAction(label=(date_object + datetime.timedelta(days=2)).strftime("%m-%d") + " (" + week_day_dict[(week_day + 2) % 7] + ")"
                                                            , data="休息#2#" + select_day)
                                    ),
                                    QuickReplyButton(
                                        action=PostbackAction(label=(date_object + datetime.timedelta(days=3)).strftime("%m-%d") + " (" + week_day_dict[(week_day + 3) % 7] + ")"
                                                            , data="休息#3#" + select_day)
                                    ),
                                    QuickReplyButton(
                                        action=PostbackAction(label=(date_object + datetime.timedelta(days=4)).strftime("%m-%d") + " (" + week_day_dict[(week_day + 4) % 7] + ")"
                                                            , data="休息#4#" + select_day)
                                    ),
                                    QuickReplyButton(
                                        action=PostbackAction(label=(date_object + datetime.timedelta(days=5)).strftime("%m-%d") + " (" + week_day_dict[(week_day + 5) % 7] + ")"
                                                            , data="休息#5#" + select_day)
                                    ),
                                    QuickReplyButton(
                                        action=PostbackAction(label=(date_object + datetime.timedelta(days=6)).strftime("%m-%d") + " (" + week_day_dict[(week_day + 6) % 7] + ")"
                                                            , data="休息#6#" + select_day)
                                    )
                                ]

                                )))
        return 0


    if "設定下班時間" in event.postback.data:
        # 當日時間
        theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
        today = str(theTime).split()[0]
        nowtime = str(theTime).split()[1]


        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()


        select_time = str(event.postback.params['time'])
        write_in_off_hour = today +" "+select_time + " "

        # 改成slot 形式
        slot_time_start_index = slot_table.index(select_time[:2] + select_time[3:])

        tmp = ""
        for i in range(slot_time_start_index,len(slot_table)):
            tmp += "slot" + slot_table[i]+" "


        sql = "update manager set off_hour = '" + write_in_off_hour + tmp + "' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()
        line_bot_api.reply_message(event.reply_token,TextSendMessage("已設定\n" +business_day[0] + "\n" + select_time + "下班" ))



        cursor.close()
        conn.close()
        return 0

    if "取消休息日設定" in event.postback.data:
        line_bot_api.reply_message(event.reply_token , TextSendMessage('已取消休息日設定，如果要重新設定，請再按一次 『營業時間管理』'))
        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        #清空manager status
        sql = "update manager set off_date = '' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()

        return 0

    if "取消下班時間設定" in event.postback.data:
        line_bot_api.reply_message(event.reply_token , TextSendMessage('已取消下班時間設定，如果要重新設定，請再按一次 『營業時間管理』'))
        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        #清空manager status
        sql = "update manager set off_hour = '' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()

        return 0


    if "確定刪除客人預約" in event.postback.data:
        line_bot_api.reply_message(event.reply_token , TextSendMessage ("已刪除"))

        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        if len(event.postback.data.split('#')) == 4: # 有userid
            # 刪除 reservation
            userName = event.postback.data.split('#')[2].split('@')[0]
            userid = event.postback.data.split('#')[1]
            date = event.postback.data.split('#')[3].split('@')[0]
            time_interval = event.postback.data.split('#')[3].split('@')[1]
            start_index = time_table.index(time_interval.split('-')[0])
            end_index = time_table.index(time_interval.split('-')[1])

            # 防止二次刪除
            for i in range(start_index,end_index):
                sql = "select slot" + slot_table[i] + " from reservation where reser_date = '" + date + "';"
                cursor.execute(sql)
                conn.commit()
                slot_result = cursor.fetchone()[0]
                name = slot_result.split('#')[0]
                if name != userName : # 預防刪除別人的預約
                    return 0

            for i in range(start_index,end_index):
                sql = "update reservation set slot" + slot_table[i] + " = null where reser_date = '" + date + "';"
                cursor.execute(sql)
                conn.commit()

            # 刪除 has_reser
            # get has_reser
            sql = "select has_reser from reservation where reser_date = '" + date + "';"
            cursor.execute(sql)
            conn.commit()
            has_reser_list = cursor.fetchone()[0].split()
            do_not_write_in_has_reser = []
            for i in range(start_index,end_index):
                do_not_write_in_has_reser.append('slot'+slot_table[i])

            re_write_has_reser_list = []

            for i in has_reser_list:
                if i in do_not_write_in_has_reser:
                    continue
                else:
                    re_write_has_reser_list.append(i)


            re_write_has_reser = ""
            for i in re_write_has_reser_list:
                re_write_has_reser += i + " "

            sql = "update reservation set has_reser = '" + re_write_has_reser + "' where reser_date = '" + date + "';"
            cursor.execute(sql)
            conn.commit()

            # 刪除 customer
            # 找has_reser 1~3
            # 然後 reser_num - 1
            sql = "select has_reser1 , has_reser2 , has_reser3 from customer where userid = '" + userid +"'"
            cursor.execute(sql)
            conn.commit()
            has_reser_result = cursor.fetchone()

            for i in range(3):
                compare_date = ''
                compare_time_interval = ''

                if has_reser_result[i] != '':
                    compare_date = has_reser_result[i].split('#')[0].split()[0]
                    compare_time_interval = has_reser_result[i].split('#')[1]
                if compare_date == date and compare_time_interval == time_interval:
                    sql = "update customer set has_reser" + str(i+1) + " = '' where userid = '" + userid + "';"
                    cursor.execute(sql)
                    conn.commit()

            # get reser_num
            sql = "select reser_num from customer where userid = '" +userid+"';"
            cursor.execute(sql)
            conn.commit()
            reser_num = int(cursor.fetchone()[0])

            # updata reser_num
            reser_num -= 1
            sql = "update customer set reser_num = '" + str(reser_num) + "' where userid = '" + userid +"';"
            cursor.execute(sql)
            conn.commit()

            cursor.close()
            conn.close()
            return 0
        else: # 沒有userid
            # 刪除 reservation
            userName = event.postback.data.split('#')[1].split('@')[0]
            date = event.postback.data.split('#')[2].split('@')[0]
            time_interval = event.postback.data.split('#')[2].split('@')[1]
            start_index = time_table.index(time_interval.split('-')[0])
            end_index = time_table.index(time_interval.split('-')[1])

            # 防止二次刪除
            for i in range(start_index,end_index):
                sql = "select slot" + slot_table[i] + " from reservation where reser_date = '" + date + "';"
                cursor.execute(sql)
                conn.commit()
                slot_result = cursor.fetchone()[0]
                name = slot_result.split('#')[0]
                if name != userName : # 預防刪除別人的預約
                    return 0
            for i in range(start_index,end_index):
                sql = "update reservation set slot" + slot_table[i] + " = null where reser_date = '" + date + "';"
                cursor.execute(sql)
                conn.commit()
            # 刪除 has_reser
            # get has_reser
            sql = "select has_reser from reservation where reser_date = '" + date + "';"
            cursor.execute(sql)
            conn.commit()
            has_reser_list = cursor.fetchone()[0].split()
            do_not_write_in_has_reser = []
            for i in range(start_index,end_index):
                do_not_write_in_has_reser.append('slot'+slot_table[i])

            re_write_has_reser_list = []

            for i in has_reser_list:
                if i in do_not_write_in_has_reser:
                    continue
                else:
                    re_write_has_reser_list.append(i)


            re_write_has_reser = ""
            for i in re_write_has_reser_list:
                re_write_has_reser += i + " "

            sql = "update reservation set has_reser = '" + re_write_has_reser + "' where reser_date = '" + date + "';"
            cursor.execute(sql)
            conn.commit()


            cursor.close()
            conn.close()
            return 0

        return 0


    if "取消刪除客人預約" in event.postback.data:
        line_bot_api.reply_message(event.reply_token , TextSendMessage ("已取消"))
        return 0

    if "刪除客人預約" in event.postback.data:
        line_bot_api.reply_message(event.reply_token,TextSendMessage("確定要刪除嗎？"
                                ,quick_reply=QuickReply(
                                    items=[
                                    QuickReplyButton(
                                        action=PostbackAction(label="確定刪除"
                                                            , data="確定" + event.postback.data)
                                    ),
                                    QuickReplyButton(
                                        action=PostbackAction(label="取消刪除"
                                                            , data="取消" + event.postback.data)
                                    )
                                ]
                                )))

        return 0

    if event.postback.data == "本週預約":
        line_bot_api.reply_message(event.reply_token, TextSendMessage("請選擇日期"
            ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[0]
                                            , data="本週預約查詢#"+date_list[0])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[1]
                                            , data="本週預約查詢#"+date_list[1])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[2]
                                            , data="本週預約查詢#"+date_list[2])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[3]
                                            , data="本週預約查詢#"+date_list[3])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[4]
                                            , data="本週預約查詢#"+date_list[4])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[5]
                                            , data="本週預約查詢#"+date_list[5])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[6]
                                            , data="本週預約查詢#"+date_list[6])
                    )
                ]
        )))


        return 0


    if "本週預約查詢" in event.postback.data:
        # 當日時間
        theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
        today = str(theTime).split()[0]
        nowtime = str(theTime).split()[1]

        # 選擇時間
        select_date = event.postback.data.split('#')[1]


        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()


        # DB if not exists insert into reservation table
        query = f"""select * from reservation where reser_date = (%s);"""
        cursor.execute(query,(select_date,))
        conn.commit()
        if cursor.fetchone() == None:
            table_columns = '(reser_date,has_reser)'
            postgres_insert_query = f"""INSERT INTO reservation {table_columns} VALUES (%s,%s);"""
            cursor.execute(postgres_insert_query, (select_date,''))
            conn.commit()

        #空白表
        null_table = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "text",
                        "text": "04-30 (四)",
                        "align": "center",
                        "size": "xl",
                        "offsetTop": "5px",
                        "weight": "bold"
                    },
                    {
                        "type": "spacer"
                    }
                    ]
                }
                ],
                "spacing": "sm",
                "paddingAll": "13px"
            }
        }


        # 設定空白表時間
        null_table['body']['contents'][0]['contents'][0]['text'] = business_day[date_list.index(select_date)]

        sql = "select * from reservation where reser_date = '" + select_date +"';"
        cursor.execute(sql)
        conn.commit()
        result = cursor.fetchone()
        start_flag = -1
        end_flag = -1
        for i in range(1,len(result)-1,1):
            #手動預約
            manul_slot = {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                {
                    "type": "text",
                    "text": "09:30-10:00",
                    "align": "center",
                    "size": "xl",
                    "gravity": "center"
                },
                {
                    "type": "button",
                    "action": {
                    "type": "postback",
                    "label": "新增",
                    "data": "time 04-30 (四) 09:30-10:00 手動預約"
                    },
                    "flex": 0,
                    "style": "primary"
                }
                ]
            }
            #分隔線
            separator = {
                "type": "separator",
                "margin": "md"
            }
            # 客人訊息
            customer_slot = {
                "type": "box",
                "layout": "vertical",
                "margin": "xxl",
                "spacing": "sm",
                "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                    {
                        "type": "text",
                        "text": "09:30-10:00",
                        "align": "center",
                        "size": "xl",
                        "gravity": "center",
                        "weight": "bold",
                        "color": "#111111"
                    }
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                    {
                        "type": "text",
                        "text": "預約人",
                        "size": "lg",
                        "color": "#111111",
                        "flex": 0
                    },
                    {
                        "type": "text",
                        "text": "林仲恩",
                        "size": "lg",
                        "color": "#111111",
                        "align": "end"
                    }
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                    {
                        "type": "text",
                        "text": "美髮項目",
                        "size": "lg",
                        "color": "#111111",
                        "flex": 0
                    },
                    {
                        "type": "text",
                        "text": "燙髮",
                        "size": "lg",
                        "color": "#111111",
                        "align": "end"
                    }
                    ]
                },
                {
                    "type": "button",
                    "action": {
                    "type": "postback",
                    "label": "刪除",
                    "data": "hello"
                    },
                    "style": "primary"
                }
                ],
                "cornerRadius": "10px",
                "backgroundColor": "#FF7F50",
                "paddingAll": "10px"
            }
            if result[i] == None: #手動新增

                if select_date == today:
                    if nowtime < time_table[i-1] and time_table[i] < '18:30':
                        # 目前時間slot
                        now_slot = time_table[i-1] + "-" + time_table[i]
                        #改時間
                        manul_slot['contents'][0]['text'] = now_slot
                        #改 postback data
                        manul_slot['contents'][1]['action']['data'] = "time " + business_day[date_list.index(select_date)] + " " + now_slot + " " + "手動預約"
                        null_table['body']['contents'].append(manul_slot)
                        null_table['body']['contents'].append(separator)
                else:
                    if time_table[i] < '18:30':
                        now_slot = time_table[i-1] + "-" + time_table[i]
                        #改時間
                        manul_slot['contents'][0]['text'] = time_table[i-1] + "-" + time_table[i]
                        #改 postback data
                        manul_slot['contents'][1]['action']['data'] = "time " + business_day[date_list.index(select_date)] +  " " + now_slot + " " + "手動預約"
                        null_table['body']['contents'].append(manul_slot)
                        null_table['body']['contents'].append(separator)

            else:
                compare1 = result[i]
                compare2 = result[i+1]

                if start_flag == -1:
                        start_flag = i

                if compare1 != compare2 :
                    end_flag = i
                    if start_flag > -1 :
                        name = compare1.split('#')[0]
                        time = time_table[start_flag-1] + "-" +time_table[end_flag]
                        service = compare1.split('#')[1]
                        customer_slot['contents'][0]['contents'][0]['text'] = time
                        customer_slot['contents'][1]['contents'][1]['text'] = name
                        customer_slot['contents'][2]['contents'][1]['text'] = service
                        #刪除按鈕 postback data
                        #manger 新增的沒有userid
                        if len(compare1.split('#')) == 3:
                            userid = compare1.split('#')[2]
                            customer_slot['contents'][3]['action']['data'] = "刪除客人預約"+ "#"+ userid  +"#"+ name + "@" + service + "#" + select_date + "@" + time
                        #客人新增的 有 userid
                        if len(compare1.split('#')) == 2:
                            customer_slot['contents'][3]['action']['data'] = "刪除客人預約"+ "#"+  name + "@" + service + "#" + select_date + "@" + time
                        null_table['body']['contents'].append(customer_slot)
                        null_table['body']['contents'].append(separator)

                        #處理完 歸零
                        start_flag = -1
                        end_flag = -1

        null_table['body']['contents'] = null_table['body']['contents'][:-1]
        null_table['body']['contents'].append(null_table['body']['contents'][0])

        line_bot_api.reply_message(event.reply_token,FlexSendMessage(alt_text="本週預約",contents=null_table
        ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[0]
                                            , data="本週預約查詢#"+date_list[0])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[1]
                                            , data="本週預約查詢#"+date_list[1])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[2]
                                            , data="本週預約查詢#"+date_list[2])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[3]
                                            , data="本週預約查詢#"+date_list[3])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[4]
                                            , data="本週預約查詢#"+date_list[4])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[5]
                                            , data="本週預約查詢#"+date_list[5])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[6]
                                            , data="本週預約查詢#"+date_list[6])
                    )
                ]
        )))




        return 0


    if event.postback.data == "今日預約":
        # 當日時間
        theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
        today = str(theTime).split()[0]
        nowtime = str(theTime).split()[1]

        # 選擇時間
        #之後要改成 event.postback.data
        select_date = today


        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        # DB if not exists insert into reservation table
        query = f"""select * from reservation where reser_date = (%s);"""
        cursor.execute(query,(select_date,))
        conn.commit()
        if cursor.fetchone() == None:
            table_columns = '(reser_date,has_reser)'
            postgres_insert_query = f"""INSERT INTO reservation {table_columns} VALUES (%s,%s);"""
            cursor.execute(postgres_insert_query, (select_date,''))
            conn.commit()

        #空白表
        null_table = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "text",
                        "text": "04-30 (四)",
                        "align": "center",
                        "size": "xl",
                        "offsetTop": "5px",
                        "weight": "bold"
                    },
                    {
                        "type": "spacer"
                    }
                    ]
                }
                ],
                "spacing": "sm",
                "paddingAll": "13px"
            }
        }


        # 設定空白表時間
        try:
            null_table['body']['contents'][0]['contents'][0]['text'] = business_day[date_list.index(select_date)]
        except ValueError:
            line_bot_api.reply_message(event.reply_token,TextSendMessage('今天是禮拜天，沒有人預約。'))
            return 0


        sql = "select * from reservation where reser_date = '" + select_date +"';"
        cursor.execute(sql)
        conn.commit()
        result = cursor.fetchone()
        start_flag = -1
        end_flag = -1
        for i in range(1,len(result)-1,1):
            #手動預約
            manul_slot = {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                {
                    "type": "text",
                    "text": "09:30-10:00",
                    "align": "center",
                    "size": "xl",
                    "gravity": "center"
                },
                {
                    "type": "button",
                    "action": {
                    "type": "postback",
                    "label": "新增",
                    "data": "time 04-30 (四) 09:30-10:00 手動預約"
                    },
                    "flex": 0,
                    "style": "primary"
                }
                ]
            }
            #分隔線
            separator = {
                "type": "separator",
                "margin": "md"
            }
            # 客人訊息
            customer_slot = {
                "type": "box",
                "layout": "vertical",
                "margin": "xxl",
                "spacing": "sm",
                "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                    {
                        "type": "text",
                        "text": "09:30-10:00",
                        "align": "center",
                        "size": "xl",
                        "gravity": "center",
                        "weight": "bold",
                        "color": "#111111"
                    }
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                    {
                        "type": "text",
                        "text": "預約人",
                        "size": "lg",
                        "color": "#111111",
                        "flex": 0
                    },
                    {
                        "type": "text",
                        "text": "林仲恩",
                        "size": "lg",
                        "color": "#111111",
                        "align": "end"
                    }
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                    {
                        "type": "text",
                        "text": "美髮項目",
                        "size": "lg",
                        "color": "#111111",
                        "flex": 0
                    },
                    {
                        "type": "text",
                        "text": "燙髮",
                        "size": "lg",
                        "color": "#111111",
                        "align": "end"
                    }
                    ]
                },
                {
                    "type": "button",
                    "action": {
                    "type": "postback",
                    "label": "刪除",
                    "data": "hello"
                    },
                    "style": "primary"
                }
                ],
                "cornerRadius": "10px",
                "backgroundColor": "#FF7F50",
                "paddingAll": "10px"
            }
            if result[i] == None: #手動新增

                if select_date == today:
                    if nowtime < time_table[i-1] and time_table[i] < '18:30':
                        # 目前時間slot
                        now_slot = time_table[i-1] + "-" + time_table[i]
                        #改時間
                        manul_slot['contents'][0]['text'] = now_slot
                        #改 postback data
                        manul_slot['contents'][1]['action']['data'] = "time " + business_day[date_list.index(today)] + " " + now_slot + " " + "手動預約"
                        null_table['body']['contents'].append(manul_slot)
                        null_table['body']['contents'].append(separator)
                else:
                    #改時間
                    manul_slot['contents'][0]['text'] = time_table[i-1] + "-" + time_table[i]
                    #改 postback data
                    manul_slot['contents'][1]['action']['data'] = "time " + business_day[date_list.index(today)] +  " " + now_slot + " " + "手動預約"
                    null_table['body']['contents'].append(manul_slot)
                    null_table['body']['contents'].append(separator)

            else: # 客人訊息
                compare1 = result[i]
                compare2 = result[i+1]

                if start_flag == -1:
                        start_flag = i

                if compare1 != compare2 :
                    end_flag = i
                    if start_flag > -1 :
                        name = compare1.split('#')[0]
                        time = time_table[start_flag-1] + "-" +time_table[end_flag]
                        service = compare1.split('#')[1]
                        customer_slot['contents'][0]['contents'][0]['text'] = time
                        customer_slot['contents'][1]['contents'][1]['text'] = name
                        customer_slot['contents'][2]['contents'][1]['text'] = service
                        #刪除按鈕 postback data
                        #manger 新增的沒有userid
                        if len(compare1.split('#')) == 3:
                            userid = compare1.split('#')[2]
                            customer_slot['contents'][3]['action']['data'] = "刪除客人預約"+ "#"+ userid  +"#"+ name + "@" + service + "#" + select_date + "@" + time
                        #客人新增的 有 userid
                        if len(compare1.split('#')) == 2:
                            customer_slot['contents'][3]['action']['data'] = "刪除客人預約"+ "#"+  name + "@" + service + "#" + select_date + "@" + time
                        null_table['body']['contents'].append(customer_slot)
                        null_table['body']['contents'].append(separator)

                        #處理完 歸零
                        start_flag = -1
                        end_flag = -1

        null_table['body']['contents'] = null_table['body']['contents'][:-1]
        null_table['body']['contents'].append(null_table['body']['contents'][0])

        line_bot_api.reply_message(event.reply_token,FlexSendMessage(alt_text="今日預約",contents=null_table))



        return 0

    if "取消刪除" in event.postback.data:
        line_bot_api.reply_message(event.reply_token,TextSendMessage("已取消"))
        return 0

    if "確定刪除" in event.postback.data:
        #TODO 刪除按兩次的情況 !!!!!!!! 注意

        line_bot_api.reply_message(event.reply_token,TextSendMessage("已經幫您刪除預約！"))
        # 刪除customer / reservation
        # reser_num - 1

        #DB setting
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        date = event.postback.data.split()[1]
        start_index = int(event.postback.data.split()[2])
        end_index = int(event.postback.data.split()[3])
        delete_index = int(event.postback.data.split()[4])
        # 05-08 14 16 1

        # 防止按兩次 刪除 造成 reser_num 一直減少
        # 檢查 是否 slot0000 = userName and slot上 service = 本身的service

        for i in range(start_index,end_index):
            sql = "select slot" + slot_table[i] + " from reservation where reser_date = '" + date + "';"
            cursor.execute(sql)
            conn.commit()
            slot_result = cursor.fetchone()[0]
            name = slot_result.split('#')[0]
            if name != userName : # 預防刪除別人的預約
                return 0



        # get reser_num
        sql = "select reser_num from customer where userid = '" +userID+"';"
        cursor.execute(sql)
        conn.commit()
        reser_num = int(cursor.fetchone()[0])

        # updata reser_num
        reser_num -= 1
        sql = "update customer set reser_num = '" + str(reser_num) + "' where userid = '" + userID +"';"
        cursor.execute(sql)
        conn.commit()

        # delete customer data
        sql = "update customer set has_reser" + str(delete_index) + " = '' where userid = '" + userID +"';"
        cursor.execute(sql)
        conn.commit()

        # delete reservation data
        # set slot0000 = '' and remove data frmo has_reser
        for i in range(start_index,end_index):
            sql = "update reservation set slot" + slot_table[i] + " = null where reser_date = '" + date + "';"
            cursor.execute(sql)
            conn.commit()

        # get has_reser
        sql = "select has_reser from reservation where reser_date = '" + date + "';"
        cursor.execute(sql)
        conn.commit()
        has_reser_list = cursor.fetchone()[0].split()
        do_not_write_in_has_reser = []
        for i in range(start_index,end_index):
            do_not_write_in_has_reser.append('slot'+slot_table[i])

        re_write_has_reser_list = []

        for i in has_reser_list:
            if i in do_not_write_in_has_reser:
                continue
            else:
                re_write_has_reser_list.append(i)


        re_write_has_reser = ""
        for i in re_write_has_reser_list:
            re_write_has_reser += i + " "

        sql = "update reservation set has_reser = '" + re_write_has_reser + "' where reser_date = '" + date + "';"
        cursor.execute(sql)
        conn.commit()


        cursor.close()
        conn.close()


        # 通知manager
        notify_mamanger_flex = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "text",
                    "text": "取消預約訊息",
                    "weight": "bold",
                    "color": "#1DB446",
                    "size": "xl",
                    "gravity": "center",
                    "align": "center"
                },
                {
                    "type": "separator",
                    "margin": "lg"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "xxl",
                    "spacing": "sm",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "text",
                            "text": "取消預約人",
                            "size": "lg",
                            "color": "#555555",
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": userName,
                            "size": "lg",
                            "color": "#111111",
                            "align": "end"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "text",
                            "text": "取消日期",
                            "size": "lg",
                            "color": "#555555",
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": date,
                            "size": "lg",
                            "color": "#111111",
                            "align": "end"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "text",
                            "text": "取消預約時間",
                            "size": "lg",
                            "color": "#555555",
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": time_table[start_index] + " - " + time_table[end_index-1],
                            "size": "lg",
                            "color": "#111111",
                            "align": "end"
                        }
                        ]
                    }
                    ]
                }
                ]
            }
        }

        line_bot_api.push_message('Ue9484510f6a0ba4d68b30d0c759949c9',FlexSendMessage(
                alt_text = '取消預約通知',
                contents = notify_mamanger_flex ))


        return 0

    if "刪除預約" in event.postback.data :
        line_bot_api.reply_message(event.reply_token, TextSendMessage("確定要刪除預約嗎？"
            ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="確定刪除"
                                            , data="確定刪除 " + event.postback.data[4:])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="取消刪除"
                                            , data="取消刪除")
                    )
                ]
        )))

        return 0

    if event.postback.data == "確認預約":
        #成功預約訊息
        line_bot_api.reply_message(event.reply_token, TextSendMessage("成功預約😃，可以到預約查詢\"修改\"或\"刪除\"喔！"))

        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()


        # get resdate
        query = "select resdate from customer where userid = '" +userID+"';"
        cursor.execute(query)
        conn.commit()
        resdate = cursor.fetchone()[0]
        size = len(resdate.split())
        date = resdate.split()[0]
        # get has_reser , and append on it
        query = "select has_reser from reservation where reser_date = '" + date +"';"
        cursor.execute(query)
        conn.commit()
        has_reser = cursor.fetchone()[0]
        # append
        for i in range(1,size,1):
            has_reser += resdate.split()[i] + " "
        query = "update reservation set has_reser = '"+ has_reser + "' where reser_date = '" + date +"';"
        cursor.execute(query)
        conn.commit()


        sql = "select reser_full_data from customer where userid = '" + userID+"';"
        cursor.execute(sql)
        conn.commit()
        reser_full_data = cursor.fetchone()[0]
        write_in_reservation = userName +"#" +reser_full_data.split("#")[2] + "#" + userID

        # 寫入reservation
        for i in range(1,size,1):
            query = "UPDATE reservation SET " + resdate.split()[i] +  "= '" + write_in_reservation + "'  where reser_date = '"  + date + "';"
            cursor.execute(query)
            conn.commit()


        # 寫入customer
        sql = "select reser_num from customer where userid = '" + userID+"';"
        cursor.execute(sql)
        conn.commit()
        reser_num = cursor.fetchone()[0]
        reser_num+=1
        if reser_num < 4:
            # 更新加一後的值回去num 並且
            query = "update customer set reser_num = '"+ str(reser_num) + "' where userid = '" + userID +"';"
            cursor.execute(query)
            conn.commit()
            # 寫入 has_reser_num
            query = "update customer set has_reser" + str(reser_num) + " = '"+ reser_full_data + "' where userid = '" + userID +"';"
            cursor.execute(query)
            conn.commit()

        notify_data = reser_full_data.split('#')[0]
        notify_time = reser_full_data.split('#')[1]
        notify_service = reser_full_data.split('#')[2]

        #清空cusomer data
        sql = "update customer set service = '' , resdate = '' ,reser_full_data = '' where userid = '" +userID+"';"
        cursor.execute(sql)
        conn.commit()


        cursor.close()
        conn.close()

        # 通知manager
        notify_mamanger_flex = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "text",
                    "text": "預約訊息",
                    "weight": "bold",
                    "color": "#1DB446",
                    "size": "xl",
                    "gravity": "center",
                    "align": "center"
                },
                {
                    "type": "separator",
                    "margin": "lg"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "xxl",
                    "spacing": "sm",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "text",
                            "text": "預約人",
                            "size": "lg",
                            "color": "#555555",
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": userName,
                            "size": "lg",
                            "color": "#111111",
                            "align": "end"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "text",
                            "text": "預約日期",
                            "size": "lg",
                            "color": "#555555",
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": notify_data,
                            "size": "lg",
                            "color": "#111111",
                            "align": "end"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "text",
                            "text": "預約時間",
                            "size": "lg",
                            "color": "#555555",
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": notify_time,
                            "size": "lg",
                            "color": "#111111",
                            "align": "end"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "text",
                            "text": "美髮項目",
                            "size": "lg",
                            "color": "#555555",
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": notify_service,
                            "size": "lg",
                            "color": "#111111",
                            "align": "end"
                        }
                        ]
                    }
                    ]
                }
                ]
            }
        }

        line_bot_api.push_message('Ue9484510f6a0ba4d68b30d0c759949c9',FlexSendMessage(
                alt_text = '預約通知',
                contents = notify_mamanger_flex ))


        return 0

    if event.postback.data == "取消預約":
        #取消預約訊息
        line_bot_api.reply_message(event.reply_token, TextSendMessage("已經幫您取消預約😖"))
        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()
        #清空cusomer data
        sql = "update customer set service = '' , resdate = '' ,reser_full_data = '' where userid = '" +userID+"';"
        cursor.execute(sql)
        conn.commit()

        cursor.close()
        conn.close()
        return 0

    if event.postback.data == "重新預約":
        line_bot_api.reply_message(event.reply_token, TextSendMessage("請選擇美髮項目"
            ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="剪髮"
                                            , data="剪髮")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="剪髮+洗髮"
                                            , data="剪髮(洗髮)")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="洗髮"
                                            , data="洗髮")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="燙髮(男)"
                                            , data="燙髮(男)")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="燙髮(女)"
                                            , data="燙髮(女)")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="染髮"
                                            , data="染髮")
                    )
                ]
        )))
        return 0

    if event.postback.data in business_day : #  選完日期後
        select_day_index = business_day.index(event.postback.data)
        select_day = date_list[select_day_index]

        #DB setting
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        # 取得下班時間
        sql = "select off_hour from manager where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()
        off_hour_result = cursor.fetchone()[0]
        off_hour_date = ''
        off_hour_time = ''
        off_hour_index = ''
        if off_hour_result != '':
            off_hour_date = off_hour_result.split()[0]
            off_hour_time = off_hour_result.split()[1]

            tmp = off_hour_result.split()
            for j in range(2, len(tmp)):
                index = slot_table.index(tmp[j][4:])
                off_hour_index += "[" + str((index * 2) +1) + "]"


        reservation = {
            "type": "carousel",
            "contents": [
                {
                "type": "bubble",
                "size": "kilo",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "text",
                            "text": "04-30 (四)",
                            "align": "center",
                            "size": "xl",
                            "offsetTop": "5px",
                            "weight": "bold"
                        },
                        {
                            "type": "spacer"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "text",
                            "text": "09:00-09:30",
                            "align": "center",
                            "size": "xl",
                            "gravity": "center"
                        },
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "預約",
                            "data": "time 04-30 (四) 09:00-09:30 預約"
                            },
                            "flex": 0,
                            "style": "primary"
                        }
                        ]
                    },
                    {
                        "type": "separator",
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "text",
                            "text": "09:30-10:00",
                            "align": "center",
                            "size": "xl",
                            "gravity": "center"
                        },
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "預約",
                            "data": "time 04-30 (四) 09:30-10:00 預約"
                            },
                            "flex": 0,
                            "style": "primary"
                        }
                        ]
                    },
                    {
                        "type": "separator",
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "text",
                            "text": "10:00-10:30",
                            "align": "center",
                            "size": "xl",
                            "gravity": "center"
                        },
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "預約",
                            "data": "time 04-30 (四) 10:00-10:30 預約"
                            },
                            "flex": 0,
                            "style": "primary"
                        }
                        ]
                    },
                    {
                        "type": "separator",
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "text",
                            "text": "10:30-11:00",
                            "align": "center",
                            "size": "xl",
                            "gravity": "center"
                        },
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "預約",
                            "data": "time 04-30 (四) 10:30-11:00 預約"
                            },
                            "flex": 0,
                            "style": "primary"
                        }
                        ]
                    },
                    {
                        "type": "separator",
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "text",
                            "text": "11:00-11:30",
                            "align": "center",
                            "size": "xl",
                            "gravity": "center"
                        },
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "預約",
                            "data": "time 04-30 (四) 11:00-11:30 預約"
                            },
                            "flex": 0,
                            "style": "primary"
                        }
                        ]
                    },
                    {
                        "type": "separator",
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "text",
                            "text": "11:30-12:00",
                            "align": "center",
                            "size": "xl",
                            "gravity": "center"
                        },
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "預約",
                            "data": "time 04-30 (四) 11:30-12:00 預約"
                            },
                            "flex": 0,
                            "style": "primary"
                        }
                        ]
                    },
                    {
                        "type": "separator",
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "text",
                            "text": "12:00-12:30",
                            "align": "center",
                            "size": "xl",
                            "gravity": "center"
                        },
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "預約",
                            "data": "time 04-30 (四) 12:00-12:30 預約"
                            },
                            "flex": 0,
                            "style": "primary"
                        }
                        ]
                    },
                    {
                        "type": "separator",
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "text",
                            "text": "12:30-13:00",
                            "align": "center",
                            "size": "xl",
                            "gravity": "center"
                        },
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "預約",
                            "data": "time 04-30 (四) 12:30-13:00 預約"
                            },
                            "flex": 0,
                            "style": "primary"
                        }
                        ]
                    },
                    {
                        "type": "separator",
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "text",
                            "text": "13:00-13:30",
                            "align": "center",
                            "size": "xl",
                            "gravity": "center"
                        },
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "預約",
                            "data": "time 04-30 (四) 13:00-13:30 預約"
                            },
                            "flex": 0,
                            "style": "primary"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "text",
                            "text": "04-30 (四)",
                            "align": "center",
                            "size": "xl",
                            "offsetTop": "5px",
                            "weight": "bold"
                        },
                        {
                            "type": "spacer"
                        }
                        ]
                    }
                    ],
                    "spacing": "sm",
                    "paddingAll": "13px"
                }
                },
                {
                "type": "bubble",
                "size": "kilo",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "text",
                            "text": "04-30 (四)",
                            "align": "center",
                            "size": "xl",
                            "offsetTop": "5px",
                            "weight": "bold"
                        },
                        {
                            "type": "spacer"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "text",
                            "text": "13:30-14:00",
                            "align": "center",
                            "size": "xl",
                            "gravity": "center"
                        },
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "預約",
                            "data": "time 04-30 (四) 13:30-14:00 預約"
                            },
                            "flex": 0,
                            "style": "primary"
                        }
                        ]
                    },
                    {
                        "type": "separator",
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "text",
                            "text": "14:00-14:30",
                            "align": "center",
                            "size": "xl",
                            "gravity": "center"
                        },
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "預約",
                            "data": "time 04-30 (四) 14:00-14:30 預約"
                            },
                            "flex": 0,
                            "style": "primary"
                        }
                        ]
                    },
                    {
                        "type": "separator",
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "text",
                            "text": "14:30-15:00",
                            "align": "center",
                            "size": "xl",
                            "gravity": "center"
                        },
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "預約",
                            "data": "time 04-30 (四) 14:30-15:00 預約"
                            },
                            "flex": 0,
                            "style": "primary"
                        }
                        ]
                    },
                    {
                        "type": "separator",
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "text",
                            "text": "15:00-15:30",
                            "align": "center",
                            "size": "xl",
                            "gravity": "center"
                        },
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "預約",
                            "data": "time 04-30 (四) 15:00-15:30 預約"
                            },
                            "flex": 0,
                            "style": "primary"
                        }
                        ]
                    },
                    {
                        "type": "separator",
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "text",
                            "text": "15:30-16:00",
                            "align": "center",
                            "size": "xl",
                            "gravity": "center"
                        },
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "預約",
                            "data": "time 04-30 (四) 15:30-16:00 預約"
                            },
                            "flex": 0,
                            "style": "primary"
                        }
                        ]
                    },
                    {
                        "type": "separator",
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "text",
                            "text": "16:00-16:30",
                            "align": "center",
                            "size": "xl",
                            "gravity": "center"
                        },
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "預約",
                            "data": "time 04-30 (四) 16:00-16:30 預約"
                            },
                            "flex": 0,
                            "style": "primary"
                        }
                        ]
                    },
                    {
                        "type": "separator",
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "text",
                            "text": "16:30-17:00",
                            "align": "center",
                            "size": "xl",
                            "gravity": "center"
                        },
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "預約",
                            "data": "time 04-30 (四) 16:30-17:00 預約"
                            },
                            "flex": 0,
                            "style": "primary"
                        }
                        ]
                    },
                    {
                        "type": "separator",
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "text",
                            "text": "17:00-17:30",
                            "align": "center",
                            "size": "xl",
                            "gravity": "center"
                        },
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "預約",
                            "data": "time 04-30 (四) 17:00-17:30 預約"
                            },
                            "flex": 0,
                            "style": "primary"
                        }
                        ]
                    },
                    {
                        "type": "separator",
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "text",
                            "text": "17:30-18:00",
                            "align": "center",
                            "size": "xl",
                            "gravity": "center"
                        },
                        {
                            "type": "button",
                            "action": {
                            "type": "postback",
                            "label": "預約",
                            "data": "time 04-30 (四) 17:30-18:00 預約"
                            },
                            "flex": 0,
                            "style": "primary"
                        }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "text",
                            "text": "04-30 (四)",
                            "align": "center",
                            "size": "xl",
                            "offsetTop": "5px",
                            "weight": "bold"
                        },
                        {
                            "type": "spacer"
                        }
                        ]
                    }
                    ],
                    "spacing": "sm",
                    "paddingAll": "13px"
                }
                }
            ]
            }



        #get select day has_reser
        # DB if not exists insert into reservation table
        query = f"""select * from reservation where reser_date = (%s);"""
        cursor.execute(query,(select_day,))
        conn.commit()
        if cursor.fetchone() == None:
            table_columns = '(reser_date,has_reser)'
            postgres_insert_query = f"""INSERT INTO reservation {table_columns} VALUES (%s,%s);"""
            cursor.execute(postgres_insert_query, (select_day,''))
            conn.commit()

        query = "select has_reser from reservation where reser_date = '" + select_day +"';"
        cursor.execute(query)
        conn.commit()
        has_reser = cursor.fetchone()[0]
        tmp = has_reser.split()
        has_reser_index = ""
        for j in range(len(tmp)):
            index = slot_table.index(tmp[j][4:])
            has_reser_index += "[" + str((index * 2) +1) + "]"

        reservation['contents'][0]['body']['contents'][0]['contents'][0]['text'] = business_day[select_day_index] + " 上午"
        reservation['contents'][0]['body']['contents'][18]['contents'][0]['text'] = business_day[select_day_index] + " 上午"
        reservation['contents'][1]['body']['contents'][0]['contents'][0]['text'] = business_day[select_day_index] + " 下午"
        reservation['contents'][1]['body']['contents'][18]['contents'][0]['text'] = business_day[select_day_index] + " 下午"

        # 當日時間超過 預約改灰
        theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
        today = str(theTime).split()[0]
        nowtime = str(theTime).split()[1]

        for j in range(1,len(reservation['contents'][0]['body']['contents']),2):

            if date_list[select_day_index] == today :
                # 當日時間超過 預約改灰
                reser_time_slot = reservation['contents'][0]['body']['contents'][j]['contents'][0]['text'].split('-')[0]
                if nowtime > reser_time_slot:
                    reservation['contents'][0]['body']['contents'][j]['contents'][1]['style'] = "secondary"

            if date_list[select_day_index] == off_hour_date:
                if ("["+str(j)+"]") in off_hour_index:
                    #換顏色 改已滿
                    reservation['contents'][0]['body']['contents'][j]['contents'][1]['style'] = "secondary"
                    reservation['contents'][0]['body']['contents'][j]['contents'][1]['action']['label'] = "下班"
                    reservation['contents'][0]['body']['contents'][j]['contents'][1]['action']['data'] = "下班"

            if ("["+str(j)+"]") in has_reser_index:
                #換顏色 改已滿
                reservation['contents'][0]['body']['contents'][j]['contents'][1]['style'] = "secondary"
                reservation['contents'][0]['body']['contents'][j]['contents'][1]['action']['label'] = "已滿"
            tmp = str(reservation['contents'][0]['body']['contents'][j]['contents'][1]['action']['data'])
            tmp = tmp[:5] + business_day[select_day_index] + tmp[14:]
            reservation['contents'][0]['body']['contents'][j]['contents'][1]['action']['data'] = tmp

        for j in range(1,len(reservation['contents'][1]['body']['contents']),2):

            if date_list[select_day_index] == today :
                # 當日時間超過 預約改灰
                reser_time_slot = reservation['contents'][1]['body']['contents'][j]['contents'][0]['text'].split('-')[0]
                if nowtime > reser_time_slot:
                    reservation['contents'][1]['body']['contents'][j]['contents'][1]['style'] = "secondary"

            if date_list[select_day_index] == off_hour_date:
                if ("["+str(j+18)+"]") in off_hour_index:
                    #換顏色 改已滿
                    reservation['contents'][1]['body']['contents'][j]['contents'][1]['style'] = "secondary"
                    reservation['contents'][1]['body']['contents'][j]['contents'][1]['action']['label'] = "下班"
                    reservation['contents'][1]['body']['contents'][j]['contents'][1]['action']['data'] = "下班"

            if ("["+str(j+18)+"]") in has_reser_index:
                #換顏色 改已滿
                reservation['contents'][1]['body']['contents'][j]['contents'][1]['style'] = "secondary"
                reservation['contents'][1]['body']['contents'][j]['contents'][1]['action']['label'] = "已滿"
            tmp = str(reservation['contents'][1]['body']['contents'][j]['contents'][1]['action']['data'])
            tmp = tmp[:5] + business_day[select_day_index] + tmp[14:]
            reservation['contents'][1]['body']['contents'][j]['contents'][1]['action']['data'] = tmp


        line_bot_api.reply_message(event.reply_token, FlexSendMessage(
                alt_text = '選擇預約時段',
                contents = reservation ,
                quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[0]
                                            , data=business_day[0])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[1]
                                            , data=business_day[1])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[2]
                                            , data=business_day[2])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[3]
                                            , data=business_day[3])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[4]
                                            , data=business_day[4])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[5]
                                            , data=business_day[5])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[6]
                                            , data=business_day[6])
                    )
                ]
        )))

        return 0

    # 手動新增預約
    if "缺預約人" in event.postback.data:


            service = event.postback.data.split('#')[1]
            resdate = event.postback.data.split('#')[2]

            #DB setting
            DATABASE_URL = os.environ['DATABASE_URL']
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            cursor = conn.cursor()

            out_of_service = ['外出','研習']

            if service not in out_of_service :
                line_bot_api.reply_message(event.reply_token,TextSendMessage("請輸入預約人姓名 :"))

                sql = "update manager set add_service = '" + service + "' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
                cursor.execute(sql)
                conn.commit()

                sql = "update manager set add_resdate = '" + resdate + "' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
                cursor.execute(sql)
                conn.commit()

                sql = "update manager set status = '輸入預約人姓名' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
                cursor.execute(sql)
                conn.commit()
                return 0
            else:
                designer = '李貞'
                sql = "update manager set add_name = '" + designer + "' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
                cursor.execute(sql)
                conn.commit()


                sql = "update manager set add_service = '" + service + "' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
                cursor.execute(sql)
                conn.commit()

                sql = "update manager set add_resdate = '" + resdate + "' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
                cursor.execute(sql)
                conn.commit()



                date = resdate.split()[0]
                time = resdate.split()[1]
                check_reser = {
                    "type": "bubble",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "text",
                            "text": "外出訊息",
                            "weight": "bold",
                            "color": "#1DB446",
                            "size": "xl",
                            "gravity": "center",
                            "align": "center"
                        },
                        {
                            "type": "separator",
                            "margin": "lg"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "margin": "xxl",
                            "spacing": "sm",
                            "contents": [
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                {
                                    "type": "text",
                                    "text": "預約日期",
                                    "size": "lg",
                                    "color": "#555555",
                                    "flex": 0
                                },
                                {
                                    "type": "text",
                                    "text": business_day[date_list.index(date)],
                                    "size": "lg",
                                    "color": "#111111",
                                    "align": "end"
                                }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                {
                                    "type": "text",
                                    "text": "預約時間",
                                    "size": "lg",
                                    "color": "#555555",
                                    "flex": 0
                                },
                                {
                                    "type": "text",
                                    "text": time,
                                    "size": "lg",
                                    "color": "#111111",
                                    "align": "end"
                                }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                {
                                    "type": "text",
                                    "text": "美髮項目",
                                    "size": "lg",
                                    "color": "#555555",
                                    "flex": 0
                                },
                                {
                                    "type": "text",
                                    "text": service,
                                    "size": "lg",
                                    "color": "#111111",
                                    "align": "end"
                                }
                                ]
                            }
                            ]
                        }
                        ]
                    }
                }
                line_bot_api.reply_message(event.reply_token,FlexSendMessage(alt_text="確認新增訊息",contents=check_reser
                                        ,quick_reply= QuickReply(
                                            items=[
                                                QuickReplyButton(
                                                    action=PostbackAction(label="確認新增"
                                                                        , data="確認新增")
                                                ),
                                                QuickReplyButton(
                                                    action=PostbackAction(label="取消新增"
                                                                        , data="取消新增")
                                                )
                                            ]
                                        )))

                #清空manager status
                sql = "update manager set status = '' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
                cursor.execute(sql)
                conn.commit()

                cursor.close()
                conn.close()


                return 0

    if "缺美髮項目和預約人" in event.postback.data:
            reser_data = event.postback.data.split('#')[1]
            date = reser_data.split()[0]
            start_time = reser_data.split()[1].split('-')[0]
            end_time = reser_data.split()[1].split('-')[1]

            # 檢查區間是否有滿
            #DB set
            DATABASE_URL = os.environ['DATABASE_URL']
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            cursor = conn.cursor()

            check_interval_list = slot_table[time_table.index(start_time):time_table.index(end_time)]

            table_columns = ''
            for i in range(len(check_interval_list)):
                table_columns += ",slot" +check_interval_list[i]


            query = f"""select {table_columns[1:]} from reservation where reser_date = (%s);"""
            cursor.execute(query,(date,))
            conn.commit()
            size = len(table_columns[1:].split(','))
            result = cursor.fetchone()
            not_none = False
            have_other_slot_isNull = False
            has_customer_index = 0
            for i in range(0,size,1):

                if result[i] != None:
                    has_customer_index = i
                    not_none = True
                    break
                else:
                    have_other_slot_isNull = True

            if have_other_slot_isNull and not_none:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(time_table[time_table.index(start_time) + has_customer_index] + " 已被預約，請重新選擇"))
                return 0


            line_bot_api.reply_message(event.reply_token, TextSendMessage("請選擇美髮項目"
            ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="剪髮"
                                            , data="缺預約人#剪髮#"+reser_data)
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="洗髮"
                                            , data="缺預約人#洗髮#"+reser_data)
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="剪髮+洗髮"
                                            , data="缺預約人#剪髮(洗髮)#"+reser_data)
                    ),QuickReplyButton(
                        action=PostbackAction(label="護髮+洗髮"
                                            , data="缺預約人#護髮(洗髮)#"+reser_data)
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="燙髮(男)"
                                            , data="缺預約人#燙髮(男)#"+reser_data)
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="燙髮(女)"
                                            , data="缺預約人#燙髮(女)#"+reser_data)
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="染髮"
                                            , data="缺預約人#染髮#"+reser_data)
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="染髮+剪髮"
                                            , data="缺預約人#染髮(剪髮)#"+reser_data)
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="外出"
                                            , data="缺預約人#外出#"+reser_data)
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="研習"
                                            , data="缺預約人#研習#"+reser_data)
                    )
                ]
            )))
            return 0

    if "time" in event.postback.data and "手動預約" in event.postback.data:
        update_bussiness_day()
        start_time = event.postback.data.split()[3].split('-')[0]
        start_time_index = time_table.index(start_time)
        date = event.postback.data.split()[1]
        line_bot_api.reply_message(event.reply_token, TextSendMessage("請問要從 "+start_time+" 到幾點？"
            ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label=time_table[start_time_index + 1]
                                            , data="缺美髮項目和預約人#"+ date + " " +start_time+ "-" +time_table[start_time_index + 1])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=time_table[start_time_index + 2]
                                            , data="缺美髮項目和預約人#"+ date + " " +start_time+ "-" +time_table[start_time_index + 2])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=time_table[start_time_index + 3]
                                            , data="缺美髮項目和預約人#"+ date + " " +start_time+ "-" +time_table[start_time_index + 3])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=time_table[start_time_index + 4]
                                            , data="缺美髮項目和預約人#"+ date + " " +start_time+ "-" +time_table[start_time_index + 4])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=time_table[start_time_index + 5]
                                            , data="缺美髮項目和預約人#"+ date + " " +start_time+ "-" +time_table[start_time_index + 5])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=time_table[start_time_index + 6]
                                            , data="缺美髮項目和預約人#"+ date + " " +start_time+ "-" +time_table[start_time_index + 6])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=time_table[start_time_index + 7]
                                            , data="缺美髮項目和預約人#"+ date + " " +start_time+ "-" +time_table[start_time_index + 7])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=time_table[start_time_index + 8]
                                            , data="缺美髮項目和預約人#"+ date + " " +start_time+ "-" +time_table[start_time_index + 8])
                    )
                ]
        )))

        #清空manger 欄位
        #DB setting
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        sql = "update manager set status = '' , add_service = '' , add_name = '' , add_resdate = '' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()

        cursor.close()
        conn.close()

        return 0

    if event.postback.data == "確認新增":
        line_bot_api.reply_message(event.reply_token , TextSendMessage("新增成功"))
        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        sql = "select add_name from manager where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()
        add_name = cursor.fetchone()[0]

        sql = "select add_service from manager where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()
        add_service = cursor.fetchone()[0]

        sql = "select add_resdate from manager where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()
        add_resdate = cursor.fetchone()[0]
        date = add_resdate.split()[0]
        time = add_resdate.split()[1]
        start_time = time.split('-')[0]
        end_time = time.split('-')[1]

        write_in_reservation = add_name + "#" + add_service
        write_in_slot = slot_table[time_table.index(start_time) : time_table.index(end_time)]
        # 寫入reservation
        for i in write_in_slot:
            query = "UPDATE reservation SET slot" + i +  "= '" + write_in_reservation + "'  where reser_date = '"  + date + "';"
            cursor.execute(query)
            conn.commit()

        #寫入 reservation 的 has_reser
        # get has_reser , and append on it
        query = "select has_reser from reservation where reser_date = '" + date +"';"
        cursor.execute(query)
        conn.commit()
        has_reser = cursor.fetchone()[0]
        # append
        for i in write_in_slot:
            has_reser += "slot" + i + " "
        query = "update reservation set has_reser = '"+ has_reser + "' where reser_date = '" + date +"';"
        cursor.execute(query)
        conn.commit()


        #清空manager 資訊
        sql = "update manager set  add_name = '' , add_service = '' , add_resdate = '' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()

        cursor.close()
        conn.close()


        return 0

    if event.postback.data == "取消新增":
        line_bot_api.reply_message(event.reply_token , TextSendMessage("已取消"))

        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        #清空manager 資訊
        sql = "update manager set  add_name = '' , add_service = '' , add_resdate = '' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()

        cursor.close()
        conn.close()

        return 0

    # 手動新增預約

    if "下班" in event.postback.data:
        line_bot_api.reply_message(event.reply_token, TextSendMessage("該時段已經下班囉！"))
        return 0

    if "time" in event.postback.data:
        update_bussiness_day()
        date = str(event.postback.data).split(" ")[1]
        compare_time = str(event.postback.data).split(" ")[3].split("-")[0]
        time = compare_time[:2]+compare_time[3:]


        # 當日時間超過
        theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
        today = str(theTime).split()[0]
        nowtime = str(theTime).split()[1]

        if today == date :
            if nowtime > compare_time:
                line_bot_api.reply_message(event.reply_token, TextSendMessage("無法預約過去的時段喔！"
                ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[0]
                                            , data=business_day[0])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[1]
                                            , data=business_day[1])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[2]
                                            , data=business_day[2])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[3]
                                            , data=business_day[3])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[4]
                                            , data=business_day[4])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[5]
                                            , data=business_day[5])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[6]
                                            , data=business_day[6])
                    )
                ]
            )))
                return 0

        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        #DB get service
        query = f"""select service from customer where userid = (%s);"""
        cursor.execute(query,(userID,))
        conn.commit()
        service = cursor.fetchone()[0]


        sql = "select reser_num from customer where userid = '" + userID+"';"
        cursor.execute(sql)
        conn.commit()
        reser_num = cursor.fetchone()[0]

        if reser_num == 3:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("最多一次只能預約三個時段喔！😥\n如果要調整時段請到\"預約查詢做調整\""))
            return 0

        if service == "":
            line_bot_api.reply_message(event.reply_token, TextSendMessage("請先選取美髮項目喔！"
            ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="剪髮"
                                            , data="剪髮")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="洗髮"
                                            , data="洗髮")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="剪髮+洗髮"
                                            , data="剪髮(洗髮)")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="護髮+洗髮"
                                            , data="護髮(洗髮)")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="燙髮(男)"
                                            , data="燙髮(男)")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="燙髮(女)"
                                            , data="燙髮(女)")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="染髮"
                                            , data="染髮")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="染髮+剪髮"
                                            , data="染髮(剪髮)")
                    )
                ]
            )))
            return 0

        # service time
        table_columns = 'reser_date'
        have_other_slot_isNull = False
        hour = ""
        index = slot_table.index(time)
        total_time = []
        reser_time = []
        if service == '剪髮':
            service_time = "30分鐘"
            total_time = slot_table[index:index + 1]
            reser_time.append(time_table[index])

            for i in range(len(total_time)):
                table_columns += ",slot" +total_time[i]
            reser_time.append(time_table[index + 1])

        if service == '剪髮(洗髮)':
            service_time = "一小時"
            total_time = slot_table[index:index + 2]
            reser_time.append(time_table[index])

            for i in range(len(total_time)):
                table_columns += ",slot" +total_time[i]
            reser_time.append(time_table[index + 2])

        if service == '洗髮(長髮)' or service == '洗髮(短髮)':
            service_time = "30分鐘"
            total_time = slot_table[index:index + 1]
            reser_time.append(time_table[index])

            for i in range(len(total_time)):
                table_columns += ",slot" +total_time[i]

            reser_time.append(time_table[index + 1])

        if service == '護髮(洗髮)':
            service_time = "一小時"
            total_time = slot_table[index:index + 2]
            reser_time.append(time_table[index])

            for i in range(len(total_time)):
                table_columns += ",slot" +total_time[i]
            reser_time.append(time_table[index + 2])

        if service == '燙髮(男)':
            service_time = "兩小時"
            total_time = slot_table[index:index + 4]
            reser_time.append(time_table[index])

            for i in range(len(total_time)):
                table_columns += ",slot" +total_time[i]

            reser_time.append(time_table[index + 4])

        if service == '燙髮(短髮)':
            service_time = "兩小時"
            total_time = slot_table[index:index + 4]
            reser_time.append(time_table[index])

            for i in range(len(total_time)):
                table_columns += ",slot" +total_time[i]

            reser_time.append(time_table[index + 4])

        if service == '燙髮(中長髮)':
            service_time = "三個半小時"
            total_time = slot_table[index:index + 7]
            reser_time.append(time_table[index])

            for i in range(len(total_time)):
                table_columns += ",slot" +total_time[i]

            reser_time.append(time_table[index + 7])

        if service == '燙髮(長髮)':
            service_time = "四小時"
            total_time = slot_table[index:index + 8]
            reser_time.append(time_table[index])

            for i in range(len(total_time)):
                table_columns += ",slot" +total_time[i]

            reser_time.append(time_table[index + 8])

        if service == '染髮(短髮)':
            service_time = "一個半小時"
            total_time = slot_table[index:index + 3]
            reser_time.append(time_table[index])

            for i in range(len(total_time)):
                table_columns += ",slot" +total_time[i]

            reser_time.append(time_table[index + 3])

        if service == '染髮(中長髮)':
            service_time = "兩小時"
            total_time = slot_table[index:index + 4]
            reser_time.append(time_table[index])

            for i in range(len(total_time)):
                table_columns += ",slot" +total_time[i]

            reser_time.append(time_table[index + 4])

        if service == '染髮(長髮)':
            service_time = "兩個半小時"
            total_time = slot_table[index:index + 5]
            reser_time.append(time_table[index])

            for i in range(len(total_time)):
                table_columns += ",slot" +total_time[i]

            reser_time.append(time_table[index + 5])

        if service == '染髮(剪髮)(短髮)':
            service_time = "兩小時"
            total_time = slot_table[index:index + 4]
            reser_time.append(time_table[index])

            for i in range(len(total_time)):
                table_columns += ",slot" +total_time[i]

            reser_time.append(time_table[index + 4])

        if service == '染髮(剪髮)(中長髮)':
            service_time = "兩個半小時"
            total_time = slot_table[index:index + 5]
            reser_time.append(time_table[index])

            for i in range(len(total_time)):
                table_columns += ",slot" +total_time[i]

            reser_time.append(time_table[index + 5])

        if service == '染髮(剪髮)(長髮)':
            service_time = "三小時"
            total_time = slot_table[index:index + 6]
            reser_time.append(time_table[index])

            for i in range(len(total_time)):
                table_columns += ",slot" +total_time[i]

            reser_time.append(time_table[index + 6])




        #DB write into reservation

        query = f"""select {table_columns} from reservation where reser_date = (%s);"""
        cursor.execute(query,(date,))
        conn.commit()
        size = len(table_columns.split(','))
        result = cursor.fetchone()
        not_none = False
        has_customer_index = 0
        for i in range(1,size,1):

            if result[i] != None:
                has_customer_index = i - 1
                not_none = True
                break
            else:
                have_other_slot_isNull = True

        if have_other_slot_isNull and not_none:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("您的美髮項目需要 "+ service_time +"\n"
                                                        + total_time[has_customer_index][:2]+":"+total_time[has_customer_index][2:] + "已有客人囉！"
                                                        ,quick_reply=QuickReply(
                                                        items=[
                                                            QuickReplyButton(
                                                                action=PostbackAction(label=business_day[0]
                                                                                    , data=business_day[0])
                                                            ),
                                                            QuickReplyButton(
                                                                action=PostbackAction(label=business_day[1]
                                                                                    , data=business_day[1])
                                                            ),
                                                            QuickReplyButton(
                                                                action=PostbackAction(label=business_day[2]
                                                                                    , data=business_day[2])
                                                            ),
                                                            QuickReplyButton(
                                                                action=PostbackAction(label=business_day[3]
                                                                                    , data=business_day[3])
                                                            ),
                                                            QuickReplyButton(
                                                                action=PostbackAction(label=business_day[4]
                                                                                    , data=business_day[4])
                                                            ),
                                                            QuickReplyButton(
                                                                action=PostbackAction(label=business_day[5]
                                                                                    , data=business_day[5])
                                                            ),
                                                            QuickReplyButton(
                                                                action=PostbackAction(label=business_day[6]
                                                                                    , data=business_day[6])
                                                            )
                                                        ]
                                                )))
            return 0

        if not_none:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("此時段已額滿！"))
            return 0
        else:
            tmp = str(event.postback.data).split()
            date_week = tmp[1] + " " + tmp[2]

            check_reser = {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "text",
                        "text": "預約訊息",
                        "weight": "bold",
                        "color": "#1DB446",
                        "size": "xl",
                        "gravity": "center",
                        "align": "center"
                    },
                    {
                        "type": "separator",
                        "margin": "lg"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "xxl",
                        "spacing": "sm",
                        "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                            {
                                "type": "text",
                                "text": "預約日期",
                                "size": "lg",
                                "color": "#555555",
                                "flex": 0
                            },
                            {
                                "type": "text",
                                "text": date_week,
                                "size": "lg",
                                "color": "#111111",
                                "align": "end"
                            }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                            {
                                "type": "text",
                                "text": "預約時間",
                                "size": "lg",
                                "color": "#555555",
                                "flex": 0
                            },
                            {
                                "type": "text",
                                "text": reser_time[0] + "-" +reser_time[1],
                                "size": "lg",
                                "color": "#111111",
                                "align": "end"
                            }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                            {
                                "type": "text",
                                "text": "美髮項目",
                                "size": "lg",
                                "color": "#555555",
                                "flex": 0
                            },
                            {
                                "type": "text",
                                "text": service,
                                "size": "lg",
                                "color": "#111111",
                                "align": "end"
                            }
                            ]
                        }
                        ]
                    }
                    ]
                },
            }
            line_bot_api.reply_message(event.reply_token, FlexSendMessage(
            alt_text = '預約訊息正確嗎？',
            contents = check_reser
            ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="確認預約"
                                            , data="確認預約")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label = "取消預約"
                                            , data = "取消預約")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label = "重新預約"
                                            , data = "重新預約")
                    )
                ]
            )))

            # write reservatin date into customer
            resdate = date
            for i in range(1,size,1):
                resdate += " " + table_columns.split(',')[i]

            sql = f"""UPDATE customer SET resdate = %s WHERE userid = %s"""
            cursor.execute(sql, (resdate , userID))
            conn.commit()
            # write full reservation data into cusotmer
            full_data = date_week + "#" +  reser_time[0] + "-" +reser_time[1] + "#" + service
            query = "update customer set reser_full_data = '" + full_data + "' where userid = '" + userID +"';"
            cursor.execute(query)
            conn.commit()

        cursor.close()
        conn.close()


        return 0


    if event.postback.data == "洗髮":
        line_bot_api.reply_message(event.reply_token, TextSendMessage("請問您是\"短髮\"還是\"長髮\""
            ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="短髮"
                                            , data="洗髮(短髮)")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="長髮"
                                            , data="洗髮(長髮)")
                    )
                ]
        )))
        return 0

    check_length_string = ["燙髮(女)","染髮","染髮(剪髮)"]
    if event.postback.data in check_length_string:
        tmp = event.postback.data
        if tmp == "燙髮(女)":
            tmp = "燙髮"
        line_bot_api.reply_message(event.reply_token, ImageSendMessage(
            original_content_url='https://imgur.com/Bwn0zuL.jpg',
            preview_image_url='https://imgur.com/Bwn0zuL.jpg'
            ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label="短髮"
                                            , data=tmp+"(短髮)")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="中長髮"
                                            , data=tmp+"(中長髮)")
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label="長髮"
                                            , data=tmp+"(長髮)")
                    )
                ]
        )))
        return 0

    accept_string = ["剪髮","剪髮(洗髮)","護髮(洗髮)","燙髮(男)","洗髮(長髮)","洗髮(短髮)","燙髮(短髮)",
    "燙髮(中長髮)","燙髮(長髮)","染髮(短髮)","染髮(中長髮)","染髮(長髮)","染髮(剪髮)(短髮)","染髮(剪髮)(中長髮)","染髮(剪髮)(長髮)"]
    if(event.postback.data in accept_string):
        line_bot_api.reply_message(event.reply_token, TextSendMessage("請選擇預約日期"
            ,quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[0]
                                            , data=business_day[0])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[1]
                                            , data=business_day[1])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[2]
                                            , data=business_day[2])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[3]
                                            , data=business_day[3])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[4]
                                            , data=business_day[4])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[5]
                                            , data=business_day[5])
                    ),
                    QuickReplyButton(
                        action=PostbackAction(label=business_day[6]
                                            , data=business_day[6])
                    )
                ]
        )))
        #DB setting
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        #DB update customer service
        service = str(event.postback.data)

        postgres_update_query = f"""UPDATE customer SET service = %s WHERE userid = %s"""
        cursor.execute(postgres_update_query, (service , userID))
        conn.commit()

        cursor.close()
        conn.close()
        return 0



static_tmp_path = os.path.join(os.path.dirname(__file__), 'static','tmp')

@handler.add(MessageEvent, message=(TextMessage,ImageMessage))
def handle_message(event):
    update_bussiness_day()
    userID = event.source.user_id
    userName = line_bot_api.get_profile(event.source.user_id).display_name
    root = ['Ue9484510f6a0ba4d68b30d0c759949c9', 'Ued44f07a33a44078eaf591e8796e3c02']

    if userID not in root:
        if isinstance(event.message, TextMessage):

            command_text = ['最新消息','聯絡我們','預約選項','作品集','預約查詢','今日預約','本週預約','最新消息管理','營業時間管理']
            if event.message.text not in command_text:
            # 提醒客人輸入非觸發訊息，要跳窗
                contact_us_flex = {
                    "type": "bubble",
                    "size": "giga",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        {
                            "type": "text",
                            "text": "在這邊傳訊息，設計師無法看到。",
                            "align": "center",
                            "offsetTop": "10px"
                        },
                        {
                            "type": "text",
                            "text": "如果需要和設計師溝通，請點選以下選項唷！",
                            "align": "center",
                            "offsetTop": "10px"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                {
                                    "type": "image",
                                    "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip13.jpg",
                                    "aspectMode": "cover",
                                    "size": "full"
                                }
                                ],
                                "cornerRadius": "100px",
                                "width": "72px",
                                "height": "72px"
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                {
                                    "type": "text",
                                    "contents": [
                                    {
                                        "type": "span",
                                        "text": "MB 髮妝",
                                        "weight": "bold",
                                        "color": "#000000",
                                        "size": "lg"
                                    }
                                    ],
                                    "size": "sm"
                                },
                                {
                                    "type": "separator",
                                    "margin": "md"
                                },
                                {
                                    "type": "text",
                                    "contents": [
                                    {
                                        "type": "span",
                                        "text": "設計師💇🏻‍♀️ 李貞",
                                        "weight": "bold",
                                        "color": "#000000"
                                    }
                                    ],
                                    "size": "sm",
                                    "margin": "md"
                                },
                                {
                                    "type": "separator",
                                    "margin": "md"
                                },
                                {
                                    "type": "text",
                                    "contents": [
                                    {
                                        "type": "span",
                                        "text": "地址🏡 屏東市中華路431號",
                                        "weight": "bold",
                                        "color": "#000000"
                                    }
                                    ],
                                    "size": "sm",
                                    "margin": "md"
                                },
                                {
                                    "type": "separator",
                                    "margin": "md"
                                },
                                {
                                    "type": "text",
                                    "contents": [
                                    {
                                        "type": "span",
                                        "text": "聯絡電話 📞 (08)-7366715",
                                        "weight": "bold",
                                        "color": "#000000"
                                    }
                                    ],
                                    "size": "sm",
                                    "margin": "md"
                                }
                                ]
                            }
                            ],
                            "spacing": "xl",
                            "paddingAll": "35px"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                            {
                                "type": "button",
                                "action": {
                                "type": "uri",
                                "label": "撥打電話",
                                "uri": "tel://087366715"
                                },
                                "height": "sm",
                                "flex": 1,
                                "gravity": "center"
                            },
                            {
                                "type": "button",
                                "action": {
                                "type": "uri",
                                "label": "聯絡設計師",
                                "uri": "https://line.me/ti/p/MY9sqcvY6h"
                                },
                                "gravity": "center",
                                "height": "sm",
                                "flex": 1
                            }
                            ],
                            "paddingAll": "20px"
                        },
                        {
                            "type": "spacer"
                        }
                        ],
                        "paddingAll": "10px"
                    }
                    }
                line_bot_api.reply_message(event.reply_token, FlexSendMessage(
                            alt_text = '聯絡資訊',
                            contents = contact_us_flex ))

                return 0


    # 確認是老闆本人
    if userID in root :
        #get manager status
        #DB set
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        sql = "select status from manager where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
        cursor.execute(sql)
        conn.commit()
        manager_status = cursor.fetchone()[0]

        if manager_status == '輸入預約人姓名':
            sql = "update manager set add_name = '" + event.message.text + "' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
            cursor.execute(sql)
            conn.commit()

            add_name = event.message.text

            sql = "select add_service from manager where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
            cursor.execute(sql)
            conn.commit()
            add_service = cursor.fetchone()[0]

            sql = "select add_resdate from manager where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
            cursor.execute(sql)
            conn.commit()
            add_resdate = cursor.fetchone()[0]
            date = add_resdate.split()[0]
            time = add_resdate.split()[1]
            #資訊正確嗎 ？
            check_reser = {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "text",
                        "text": "預約訊息",
                        "weight": "bold",
                        "color": "#1DB446",
                        "size": "xl",
                        "gravity": "center",
                        "align": "center"
                    },
                    {
                        "type": "separator",
                        "margin": "lg"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "xxl",
                        "spacing": "sm",
                        "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                            {
                                "type": "text",
                                "text": "預約人",
                                "size": "lg",
                                "color": "#555555",
                                "flex": 0
                            },
                            {
                                "type": "text",
                                "text": add_name,
                                "size": "lg",
                                "color": "#111111",
                                "align": "end"
                            }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                            {
                                "type": "text",
                                "text": "預約日期",
                                "size": "lg",
                                "color": "#555555",
                                "flex": 0
                            },
                            {
                                "type": "text",
                                "text": business_day[date_list.index(date)],
                                "size": "lg",
                                "color": "#111111",
                                "align": "end"
                            }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                            {
                                "type": "text",
                                "text": "預約時間",
                                "size": "lg",
                                "color": "#555555",
                                "flex": 0
                            },
                            {
                                "type": "text",
                                "text": time,
                                "size": "lg",
                                "color": "#111111",
                                "align": "end"
                            }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                            {
                                "type": "text",
                                "text": "美髮項目",
                                "size": "lg",
                                "color": "#555555",
                                "flex": 0
                            },
                            {
                                "type": "text",
                                "text": add_service,
                                "size": "lg",
                                "color": "#111111",
                                "align": "end"
                            }
                            ]
                        }
                        ]
                    }
                    ]
                }
            }
            line_bot_api.reply_message(event.reply_token,FlexSendMessage(alt_text="確認新增訊息",contents=check_reser
                                    ,quick_reply= QuickReply(
                                        items=[
                                            QuickReplyButton(
                                                action=PostbackAction(label="確認新增"
                                                                    , data="確認新增")
                                            ),
                                            QuickReplyButton(
                                                action=PostbackAction(label="取消新增"
                                                                    , data="取消新增")
                                            )
                                        ]
                                    )))

            #清空manager status
            sql = "update manager set status = '' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
            cursor.execute(sql)
            conn.commit()

            cursor.close()
            conn.close()

            return 0

        if manager_status == '輸入最新消息':
            line_bot_api.reply_message(event.reply_token,TextSendMessage("已新增完成🗒"))

            # get the url list
            sql = "select pic_1,pic_2 from manager where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
            cursor.execute(sql)
            conn.commit()
            img_list = cursor.fetchone()

            # insert into news_table
            # update to the portfolio
            table_columns = '(news,news_p1,news_p2)'
            sql = f"""insert into news_table {table_columns} values (%s,%s,%s)"""
            cursor.execute(sql , (event.message.text,img_list[0],img_list[1]))
            conn.commit()


            #reset pic_num ,reset img_url
            sql = "update manager set news='',status='',pic_num = '0' ,pic_1 = '', pic_2 = '', pic_3 = '' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
            cursor.execute(sql)
            conn.commit()

            cursor.close()
            conn.close()

            line_bot_api.reply_message(event.reply_token,TextSendMessage("已新增完成🗒"))
            return 0

        #上傳圖片
        if manager_status == "上傳一張圖片":
            need_pic_num = 1
            ext = 'jpg'
            message_content = line_bot_api.get_message_content(event.message.id)

            with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix=ext + '-', delete=False) as tf:
                for chunk in message_content.iter_content():
                    tf.write(chunk)
                tempfile_path = tf.name

            dist_path = tempfile_path + '.' + ext
            dist_name = os.path.basename(dist_path)
            os.rename(tempfile_path, dist_path)
            try:
                client = ImgurClient(client_id, client_secret, access_token, refresh_token)
                config = {
                    'album': works_album_id,
                    'name': 'Catastrophe!',
                    'title': 'Catastrophe!',
                    'description': 'Cute kitten being cute on '
                }
                path = os.path.join('static', 'tmp', dist_name)
                img_url = client.upload_from_path(path, config=config, anon=False)
                os.remove(path)

                # get pic#
                sql = "select pic_num from manager where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
                cursor.execute(sql)
                conn.commit()
                pic_num = int(cursor.fetchone()[0])
                pic_num += 1


                # update pic# and update the url
                sql = "update manager set pic_num='" + str(pic_num) +"' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
                cursor.execute(sql)
                conn.commit()

                sql = "update manager set pic_" + str(pic_num) + " ='" + img_url['link'] + "' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
                cursor.execute(sql)
                conn.commit()

                # if pic# == need_pic_num , then reply
                if pic_num == need_pic_num:
                    # reply text
                    line_bot_api.reply_message(event.reply_token, TextSendMessage("再來輸入要告訴客人的最新消息😄"))
                    # set manager status
                    #DB setting
                    DATABASE_URL = os.environ['DATABASE_URL']
                    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
                    cursor = conn.cursor()

                    sql = "update manager set status = '輸入最新消息' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
                    cursor.execute(sql)
                    conn.commit()

                    cursor.close()
                    conn.close()

                return 0
            except Exception as e:
                print(e)
            return 0

        if manager_status == "上傳兩張圖片":
            need_pic_num = 2
            ext = 'jpg'
            message_content = line_bot_api.get_message_content(event.message.id)

            with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix=ext + '-', delete=False) as tf:
                for chunk in message_content.iter_content():
                    tf.write(chunk)
                tempfile_path = tf.name

            dist_path = tempfile_path + '.' + ext
            dist_name = os.path.basename(dist_path)
            os.rename(tempfile_path, dist_path)
            try:
                client = ImgurClient(client_id, client_secret, access_token, refresh_token)
                config = {
                    'album': works_album_id,
                    'name': 'Catastrophe!',
                    'title': 'Catastrophe!',
                    'description': 'Cute kitten being cute on '
                }
                path = os.path.join('static', 'tmp', dist_name)
                img_url = client.upload_from_path(path, config=config, anon=False)
                os.remove(path)

                # get pic#
                sql = "select pic_num from manager where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
                cursor.execute(sql)
                conn.commit()
                pic_num = int(cursor.fetchone()[0])
                pic_num += 1


                # update pic# and update the url
                sql = "update manager set pic_num='" + str(pic_num) +"' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
                cursor.execute(sql)
                conn.commit()

                sql = "update manager set pic_" + str(pic_num) + " ='" + img_url['link'] + "' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
                cursor.execute(sql)
                conn.commit()

                # if pic# == need_pic_num , then reply
                if pic_num == need_pic_num:
                    # reply text
                    line_bot_api.reply_message(event.reply_token, TextSendMessage("再來輸入要告訴客人的最新消息😄"))
                    # set manager status
                    #DB setting
                    DATABASE_URL = os.environ['DATABASE_URL']
                    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
                    cursor = conn.cursor()

                    sql = "update manager set status = '輸入最新消息' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
                    cursor.execute(sql)
                    conn.commit()

                    cursor.close()
                    conn.close()

                    return 0
            except Exception as e:
                print(e)
            return 0

        if '上傳圖片' in manager_status :
            style = manager_status.split('#')[1]
            need_pic_num = 0
            if style == "樣式一":
                need_pic_num = 1
            if style == "樣式二":
                need_pic_num = 2
            if style == "樣式三":
                need_pic_num = 3


            ext = 'jpg'
            message_content = line_bot_api.get_message_content(event.message.id)

            with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix=ext + '-', delete=False) as tf:
                for chunk in message_content.iter_content():
                    tf.write(chunk)
                tempfile_path = tf.name

            dist_path = tempfile_path + '.' + ext
            dist_name = os.path.basename(dist_path)
            os.rename(tempfile_path, dist_path)
            try:
                client = ImgurClient(client_id, client_secret, access_token, refresh_token)
                config = {
                    'album': works_album_id,
                    'name': 'Catastrophe!',
                    'title': 'Catastrophe!',
                    'description': 'Cute kitten being cute on '
                }
                path = os.path.join('static', 'tmp', dist_name)
                img_url = client.upload_from_path(path, config=config, anon=False)
                os.remove(path)

                # get pic#
                sql = "select pic_num from manager where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
                cursor.execute(sql)
                conn.commit()
                pic_num = int(cursor.fetchone()[0])
                pic_num += 1


                # update pic# and update the url
                sql = "update manager set pic_num='" + str(pic_num) +"' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
                cursor.execute(sql)
                conn.commit()

                sql = "update manager set pic_" + str(pic_num) + " ='" + img_url['link'] + "' where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
                cursor.execute(sql)
                conn.commit()

                # if pic# == need_pic_num , then reply
                if pic_num == need_pic_num:
                    # preview the result and ask yes or no
                    # get the pic_url
                    # get the theme
                    if '樣式一' in manager_status:
                        sql = "select pic_1 from manager where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
                        cursor.execute(sql)
                        conn.commit()
                        img_list = cursor.fetchone()

                        theme1 = {
                            "type": "bubble",
                            "size": "giga",
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "contents": [
                                    {
                                        "type": "image",
                                        "url": img_list[0],
                                        "aspectMode": "cover",
                                        "size": "full",
                                        "aspectRatio": "50:100"
                                    }
                                    ]
                                }
                                ],
                                "paddingAll": "10px"
                            }
                        }

                        line_bot_api.reply_message(event.reply_token, FlexSendMessage('預覽樣式一',theme1,quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=PostbackAction(label="上傳至『剪髮相簿』"
                                                            , data="上傳剪髮相簿")
                                    ),
                                    QuickReplyButton(
                                        action=PostbackAction(label="上傳至『燙髮相簿』"
                                                            , data="上傳燙髮相簿")
                                    ),
                                    QuickReplyButton(
                                        action=PostbackAction(label="上傳至『染髮相簿』"
                                                            , data="上傳染髮相簿")
                                    ),
                                    QuickReplyButton(
                                        action=PostbackAction(label="重新上傳"
                                                            , data="新增作品")
                                    )
                                ]
                                )
                        ))

                    if '樣式二' in manager_status:
                        sql = "select pic_1,pic_2 from manager where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
                        cursor.execute(sql)
                        conn.commit()
                        img_list = cursor.fetchone()

                        theme2 = {
                            "type": "bubble",
                            "size": "giga",
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "contents": [
                                    {
                                        "type": "image",
                                        "url": img_list[0],
                                        "aspectMode": "cover",
                                        "size": "full",
                                        "aspectRatio": "100:100"
                                    },
                                    {
                                        "type": "image",
                                        "url": img_list[1],
                                        "aspectMode": "cover",
                                        "size": "full",
                                        "aspectRatio": "100:100"
                                    }
                                    ]
                                }
                                ],
                                "paddingAll": "10px"
                            }
                        }

                        line_bot_api.reply_message(event.reply_token, FlexSendMessage('預覽樣式二',theme2,quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=PostbackAction(label="上傳至『剪髮相簿』"
                                                            , data="上傳剪髮相簿")
                                    ),
                                    QuickReplyButton(
                                        action=PostbackAction(label="上傳至『燙髮相簿』"
                                                            , data="上傳燙髮相簿")
                                    ),
                                    QuickReplyButton(
                                        action=PostbackAction(label="上傳至『染髮相簿』"
                                                            , data="上傳染髮相簿")
                                    ),
                                    QuickReplyButton(
                                        action=PostbackAction(label="重新上傳"
                                                            , data="新增作品")
                                    )
                                ]
                                )
                        ))

                    if '樣式三' in manager_status:
                        sql = "select pic_1,pic_2,pic_3 from manager where userid = 'Ue9484510f6a0ba4d68b30d0c759949c9'"
                        cursor.execute(sql)
                        conn.commit()
                        img_list = cursor.fetchone()

                        theme3 = {
                            "type": "bubble",
                            "size": "giga",
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "contents": [
                                    {
                                        "type": "image",
                                        "url": img_list[0],
                                        "aspectMode": "cover",
                                        "size": "full"
                                    }
                                    ],
                                    "cornerRadius": "200px"
                                },
                                {
                                    "type": "box",
                                    "layout": "horizontal",
                                    "contents": [
                                    {
                                        "type": "image",
                                        "url": img_list[1],
                                        "aspectMode": "cover",
                                        "size": "5xl",
                                        "aspectRatio": "150:300"
                                    },
                                    {
                                        "type": "image",
                                        "url": img_list[2],
                                        "aspectMode": "cover",
                                        "size": "5xl",
                                        "aspectRatio": "150:300"
                                    }
                                    ]
                                }
                                ],
                                "paddingAll": "10px"
                            }
                        }

                        line_bot_api.reply_message(event.reply_token, FlexSendMessage('預覽樣式三',theme3,quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=PostbackAction(label="上傳至『剪髮相簿』"
                                                            , data="上傳剪髮相簿")
                                    ),
                                    QuickReplyButton(
                                        action=PostbackAction(label="上傳至『燙髮相簿』"
                                                            , data="上傳燙髮相簿")
                                    ),
                                    QuickReplyButton(
                                        action=PostbackAction(label="上傳至『染髮相簿』"
                                                            , data="上傳染髮相簿")
                                    ),
                                    QuickReplyButton(
                                        action=PostbackAction(label="重新上傳"
                                                            , data="新增作品")
                                    )
                                ]
                                )
                        ))

                    return 0



                # line_bot_api.reply_message(
                #     event.reply_token,
                #     TextSendMessage(text='上傳成功'))
            except Exception as e:
                print(e)
            return 0

if __name__ == "__main__":
    app.run()
