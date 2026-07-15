from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from datetime import datetime, timedelta
import json
import os
import threading
import time
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials


app = Flask(__name__)


load_dotenv()


CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
USER_ID = os.getenv("USER_ID")
GROUP_ID = os.getenv("GROUP_ID")


scheduler = BackgroundScheduler()


line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


DATA_FILE = "./shows.json"


# =====================
# Google Sheets 設定
# =====================

SHEET_NAME = "你的試算表名稱"


def connect_google_sheet():

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]


    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "service_account.json",
        scope
    )


    client = gspread.authorize(creds)


    sheet = client.open(
        SHEET_NAME
    ).sheet1


    return sheet


# =====================
# 資料處理
# =====================

def load_data():

    if not os.path.exists(DATA_FILE):
        return []

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)



def save_data(data):

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )


def get_sheet_shows():

    sheet = connect_google_sheet()

    records = sheet.get_all_records()

    return records



def find_ticket_master(show_name):

    shows = get_sheet_shows()


    for show in shows:

        if show["演唱會名稱"] == show_name:

            return show["搶票大師"]


    return None



def get_line_id(nickname):

    sheet = connect_google_sheet()

    users = sheet.get_all_records()


    for user in users:

        if user["暱稱"] == nickname:

            return user["LINE_ID"]


    return None



# =====================
# 排序功能
# =====================

def sort_shows(shows):
    # 搶票時間排序

    return sorted(
        shows,
        key=lambda x: datetime.strptime(
            x.get("搶票時間", "9999/12/31 23:59"),
            "%Y/%m/%d %H:%M"
        )
    )



def sort_by_show_date(shows):
    # 演出日期排序

    return sorted(
        shows,
        key=lambda x: datetime.strptime(
            x.get("演出日期", "9999/12/31"),
            "%Y/%m/%d"
        )
    )



def sort_by_pickup_date(shows):
    # 取票日期排序

    return sorted(
        shows,
        key=lambda x: datetime.strptime(
            x.get("取票日期", "9999/12/31"),
            "%Y/%m/%d"
        )
    )



# =====================
# 共用列表功能
# =====================

def get_waiting_shows():

    shows = sort_shows(
        load_data()
    )

    waiting = []

    for show in shows:

        show.setdefault(
            "搶票狀態",
            "等待搶票"
        )

        if show["搶票狀態"] == "等待搶票":

            try:

                ticket_time = datetime.strptime(
                    show["搶票時間"],
                    "%Y/%m/%d %H:%M"
                )


                if ticket_time > datetime.now() + timedelta(hours=8):

                    waiting.append(show)


            except Exception as e:

                print(
                    "搶票時間錯誤：",
                    e
                )


    return waiting



def get_pickup_shows():

    shows = sort_by_pickup_date(
        load_data()
    )

    pickup = []

    for show in shows:

        show.setdefault(
            "取票狀態",
            "未取票"
        )

        if (
            show.get("取票日期")
            and show["取票狀態"] == "未取票"
        ):

            pickup.append(show)


    return pickup



def get_all_shows():

    shows = sort_by_show_date(
        load_data()
    )

    return shows


# =====================
# 提醒功能
# =====================

def check_reminders():

    print("提醒檢查執行", datetime.now())

    now = datetime.now() + timedelta(hours=8)

    today = now.strftime("%Y/%m/%d")

    shows = load_data()

    print("目前演出資料：", shows)

    for show in shows:

        show.setdefault("提醒", {
            "前一天": False,
            "30分鐘": False,
            "10分鐘": False,
            "取票": False,
            "演出日": False
        })

        show.setdefault("搶票狀態", "等待搶票")
        show.setdefault("取票狀態", "未取票")


        try:

            ticket_time = datetime.strptime(
                show["搶票時間"],
                "%Y/%m/%d %H:%M"
            )


            # 前一天 21:00

            remind_time = (
                ticket_time - timedelta(days=1)
            ).replace(
                hour=21,
                minute=0,
                second=0,
                microsecond=0
            )


            if (
                remind_time <= now <= remind_time + timedelta(minutes=1)
                and not show["提醒"]["前一天"]
            ):

                line_bot_api.push_message(
                    GROUP_ID,
                    TextSendMessage(
                        text=(
                            "⏰ 明日搶票提醒\n\n"
                            f"🎤 {show['演出名稱']}\n"
                            f"🎟 搶票時間：{show['搶票時間']}\n"
                            f"🌐 售票平台：{show['售票平台']}"
                        )
                    )
                )


                show["提醒"]["前一天"] = True
                save_data(shows)


            diff = ticket_time - now

            print(
                "演出:",
                show["演出名稱"],
                "搶票:",
                ticket_time,
                "剩餘:",
                diff
            )


            # 前30分鐘

            if (
                timedelta(minutes=29)
                <= diff <= timedelta(minutes=31)
                and not show["提醒"]["30分鐘"]
            ):

                line_bot_api.push_message(
                    GROUP_ID,
                    TextSendMessage(
                        text=(
                            "⏰ 搶票倒數 30 分鐘\n\n"
                            f"🎤 {show['演出名稱']}\n"
                            f"🎟 搶票時間：{show['搶票時間']}\n"
                            f"🌐 售票平台：{show['售票平台']}\n"
                            f"📝 備註：{show['備註'] if show['備註'] else '無'}"
                        )
                    )
                )


                show["提醒"]["30分鐘"] = True
                save_data(shows)


            # 前10分鐘

            if (
                timedelta(minutes=9)
                <= diff <= timedelta(minutes=11)
                and not show["提醒"]["10分鐘"]
            ):

                line_bot_api.push_message(
                    GROUP_ID,
                    TextSendMessage(
                        text=(
                            "🔐 搶票倒數 10 分鐘\n\n"
                            f"🎤 {show['演出名稱']}\n"
                            f"🎟 搶票時間：{show['搶票時間']}\n"
                            f"🌐 售票平台：{show['售票平台']}\n"
                            f"💰 價格張數：{show['價格張數']}\n"
                            f"📝 備註：{show['備註'] if show['備註'] else '無'}"
                        )
                    )
                )

                show["提醒"]["10分鐘"] = True
                save_data(shows)


        except Exception as e:

            print(
                f"提醒錯誤：{e}"
            )


        # 取票提醒
        if show.get("取票日期"):

            pickup_time = datetime.strptime(
                show["取票日期"] + " 12:00",
                "%Y/%m/%d %H:%M"
            )

            if (
                pickup_time <= now < pickup_time + timedelta(minutes=1)
                and not show["提醒"]["取票"]
            ):

                line_bot_api.push_message(
                    GROUP_ID,
                    TextSendMessage(
                        text=(
                            "🎫 取票提醒\n\n"
                            f"🎤 {show['演出名稱']}\n"
                            "今天可以取票囉！"
                        )
                    )
                )

                show["提醒"]["取票"] = True
                save_data(shows)


def reminder_loop():

    while True:

        now = datetime.now()

        # 等到下一個整分
        sleep_seconds = 60 - now.second

        time.sleep(sleep_seconds)

        try:
            check_reminders()

        except Exception as e:
            print("提醒錯誤：", e)

# =====================
# LINE Callback
# =====================

@app.route("/callback", methods=["POST"])
def callback():

    signature = request.headers["X-Line-Signature"]

    body = request.get_data(as_text=True)


    handler.handle(
        body,
        signature
    )


    return "OK"



# =====================
# 訊息處理
# =====================

@handler.add(
    MessageEvent,
    message=TextMessage
)
def handle_message(event):

    text = event.message.text.strip()


    # =====================
    # 測試提醒
    # =====================

    if text == "測試提醒":


        line_bot_api.push_message(
            GROUP_ID,
            TextSendMessage(
                text="🔔 測試成功！\n群組提醒功能已連線。"
            )
        )


        reply = "已發送測試提醒"



    # =====================
    # 搶票列表功能
    # =====================

    elif text == "搶票列表":

        waiting = get_waiting_shows()


        if not waiting:

            reply = "目前沒有待搶票演出"


        else:

            reply = "🎟️ 搶票列表\n"


            for i, show in enumerate(
                waiting,
                start=1
            ):

                reply += (
                    f"\n{i}.\n"
                    f"🎤 {show['演出名稱']}\n"
                    f"🎟 {show['搶票時間']}\n"
                    f"🌐 售票平台：{show['售票平台']}\n"
                    f"📝 備註：{show['備註'] if show['備註'] else '無'}\n"
                    f"📌 狀態：{show.get('搶票狀態','等待搶票')}\n"
                )


            reply += (
                "\n👉 查看詳細資料：\n"
                "輸入：查看 1"
            )


    # =====================
    # 取票列表功能
    # =====================

    elif text == "取票列表":

        pickup_list = get_pickup_shows()


        if not pickup_list:

            reply = "目前沒有取票資料"


        else:

            reply = "🎫 取票列表\n"


            for i, show in enumerate(
                pickup_list,
                start=1
            ):

                reply += (
                    f"\n{i}.\n"
                    f"🎤 {show['演出名稱']}\n"
                    f"📅 取票日期：{show['取票日期']}\n"
                    f"📌 狀態：{show.get('取票狀態','未取票')}\n"
                )


    # =====================
    # 演出列表功能
    # =====================

    elif text == "演出列表":


        shows = sort_by_show_date(
            load_data()
        )


        if not shows:

            reply = "目前沒有演出資料"


        else:

            reply = "🎫 演出列表\n"


            for i, show in enumerate(
                shows,
                start=1
            ):

                reply += (
                    f"\n{i}.\n"
                    f"🎤 {show['演出名稱']}\n"
                    f"📅 演出日期：{show['演出日期']}\n"
                    f"🎟 搶票：{show.get('搶票狀態','等待搶票')}\n"
                    f"🎫 取票：{show.get('取票狀態','未取票')}\n"
                )


            reply += (
                "\n👉 查看詳細資料：\n"
                "輸入：查看 1"
            )


    # =====================
    # 新增功能
    # =====================

    elif text.startswith("新增"):

        try:

            lines = text.split("\n")

            data = {}


            for line in lines:

                if "：" in line:

                    key, value = line.split("：", 1)

                    data[key.strip()] = value.strip()



            event_date = datetime.strptime(
                data["演出日期"],
                "%Y/%m/%d"
            )


            ticket_text = data.get(
                "取票日期",
                ""
            )


            if "天前" in ticket_text:

                days = int(
                    ticket_text.replace(
                        "天前",
                        ""
                    )
                )

                ticket_date = (
                    event_date -
                    timedelta(days=days)
                ).strftime("%Y/%m/%d")


            else:

                ticket_date = ticket_text



            show = {

                "演出名稱":
                    data.get("演出名稱", ""),

                "演出日期":
                    data.get("演出日期", ""),

                "搶票時間":
                    data.get("搶票時間", ""),

                "價格張數":
                    data.get("價格張數", ""),

                "售票平台":
                    data.get("售票平台", ""),

                "取票日期":
                    ticket_date,

                "備註":
                    data.get("備註", ""),

                "搶票狀態": "等待搶票",
                "取票狀態": "未取票",


                "提醒": {
                    "前一天": False,
                    "30分鐘": False,
                    "10分鐘": False,
                    "取票": False,
                    "演出日": False
                }
            }



            shows = load_data()

            shows.append(show)

            print("準備寫入：", shows)

            save_data(shows)

            print("寫入完成")


            reply = (

                "✅ 新增成功\n\n"

                f"🎤 {show['演出名稱']}\n"

                f"📅 演出日期：{show['演出日期']}\n"

                f"🎟 搶票時間：{show['搶票時間']}\n"

                f"💰 {show['價格張數']}\n"

                f"🌐 {show['售票平台']}\n"

                f"🎫 取票提醒：{show['取票日期']}\n"

                f"📝 {show['備註']}"
            )


        except Exception as e:

            print(e)

            reply = "❌ 新增格式錯誤"



    # =====================
    # 查看功能
    # =====================

    elif text.startswith("查看"):

        shows = get_all_shows()


        try:

            index = int(
                text.replace(
                    "查看",
                    ""
                ).strip()
            ) - 1


            if index < 0 or index >= len(shows):

                reply = "❌ 找不到這筆演出"


            else:

                show = shows[index]


                note = (
                    show["備註"]
                    if show["備註"]
                    else "無"
                )


                reply = (

                    "🎫 演出資訊\n\n"

                    f"🎤 {show['演出名稱']}\n\n"

                    "📅 演出日期\n"
                    f"{show['演出日期']}\n\n"

                    "🎟 搶票時間\n"
                    f"{show['搶票時間']}\n\n"

                    "💰 價格張數\n"
                    f"{show['價格張數']}\n\n"

                    "🌐 售票平台\n"
                    f"{show['售票平台']}\n\n"

                    "📌 搶票狀態\n"
                    f"{show.get('搶票狀態','等待搶票')}\n\n"

                    "🎫 取票狀態\n"
                    f"{show.get('取票狀態','未取票')}\n\n"

                    "📝 備註\n"
                    f"{note}"
                )


        except Exception as e:

            print(e)

            reply = "請輸入格式：\n查看 1"



    # =====================
    # 修改功能 v0.7.0
    # =====================

    elif text.startswith("修改"):


        shows = get_all_shows()


        try:

            lines = text.split("\n")


            index = int(
                lines[0]
                .replace("修改", "")
                .strip()
            ) - 1



            if index < 0 or index >= len(shows):

                reply = "❌ 找不到這筆演出"


            elif len(lines) == 1:

                reply = (
                    "✏️ 修改演出\n\n"
                    "請輸入要修改的內容\n\n"
                    "例如：\n"
                    "修改 1\n"
                    "備註：會員預售"
                )


            else:

                show = shows[index]


                update_data = {}


                for line in lines[1:]:

                    if "：" in line:

                        key, value = line.split(
                            "：",
                            1
                        )

                        update_data[
                            key.strip()
                        ] = value.strip()



                for key, value in update_data.items():

                    if key in show:

                        show[key] = value



                save_data(
                    shows
                )


                note = (
                    show["備註"]
                    if show["備註"]
                    else "無"
                )


                reply = (

                    "✅ 修改成功\n\n"

                    f"🎤 {show['演出名稱']}\n\n"

                    "📅 演出日期\n"
                    f"{show['演出日期']}\n\n"

                    "🎟 搶票時間\n"
                    f"{show['搶票時間']}\n\n"

                    "💰 價格 / 張數\n"
                    f"{show['價格張數']}\n\n"

                    "🌐 售票平台\n"
                    f"{show['售票平台']}\n\n"

                    "📝 備註\n"
                    f"{note}"
                )


        except Exception as e:

            print(e)

            reply = "請輸入格式：\n修改 1"



    # =====================
    # 完成搶票
    # =====================

    elif text.startswith("完成搶票"):

        shows = sort_shows(load_data())

        waiting = []

        for show in shows:

            show.setdefault("搶票狀態", "等待搶票")

            if show["搶票狀態"] == "等待搶票":

                waiting.append(show)

        try:

            lines = text.split("\n")


            index = int(
                lines[0]
                .replace(
                    "完成搶票",
                    ""
                )
                .strip()
            ) - 1

            if index < 0 or index >= len(waiting):

                reply = "❌ 找不到這筆搶票資料"

            else:

                show = waiting[index]


                show["搶票狀態"] = "已搶票"


                show.setdefault(
                    "搶票大師",
                    ""
                )

                show.setdefault(
                    "參加者",
                    []
                )


                for line in lines[1:]:


                    if line.startswith("搶票大師："):

                        show["搶票大師"] = (
                            line
                            .replace(
                                "搶票大師：",
                                ""
                            )
                            .strip()
                        )
            

                    elif line.startswith("參加者："):

                        members = (
                            line
                            .replace(
                                "參加者：",
                                ""
                            )
                            .strip()
                        )


                        show["參加者"] = [
                            x.strip()
                            for x in members.split("、")
                        ]


                save_data(shows)


                reply = (
                    "✅ 已完成搶票\n\n"
                    f"🎤 {show['演出名稱']}\n"
                    f"🎟 搶票大師：{show['搶票大師']}\n"
                    f"👥 參加者：{'、'.join(show['參加者'])}\n"
                    "📌 狀態：已搶票"
                )


        except Exception as e:

            print(e)

            reply = "請輸入格式：\n完成搶票 1"


    # =====================
    # 完成取票
    # =====================

    elif text.startswith("完成取票"):


        pickup_list = get_pickup_shows()


        try:

            index = int(
                text.replace(
                    "完成取票",
                    ""
                ).strip()
            ) - 1



            if index < 0 or index >= len(pickup_list):

                reply = "❌ 找不到這筆取票資料"


            else:

                target = pickup_list[index]


                shows = load_data()


                for show in shows:

                    if (
                        show.get("演出名稱") == target.get("演出名稱")
                        and show.get("演出日期") == target.get("演出日期")
                    ):

                        show["取票狀態"] = "已取票"

                        save_data(shows)

                        break



                reply = (

                    "✅ 已完成取票\n\n"

                    f"🎤 {target['演出名稱']}\n"

                    f"📅 演出日期：{target['演出日期']}\n"

                    "🎫 狀態：已取票"
                )



        except Exception as e:

            print(e)

            reply = "請輸入格式：\n完成取票 1"
    


    # =====================
    # 刪除功能
    # =====================

    elif text.startswith("刪除"):


        shows = get_all_shows()


        try:

            index = int(
                text.replace(
                    "刪除",
                    ""
                ).strip()
            ) - 1



            if index < 0 or index >= len(shows):

                reply = "❌ 找不到這筆演出"


            else:

                deleted = shows.pop(index)

                save_data(shows)


                reply = (

                    "✅ 刪除成功\n\n"

                    f"🎤 {deleted['演出名稱']}\n"

                    f"📅 演出日期：{deleted['演出日期']}"
                )


        except Exception as e:

            print(e)

            reply = "請輸入格式：\n刪除 1"



    # =====================
    # ID
    # =====================

    elif text == "ID":


        if event.source.type == "group":

            reply = event.source.group_id

        else:

            reply = event.source.user_id



    else:

        reply = "❓ 不知道這個指令"



    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )



if __name__ == "__main__":


    threading.Thread(
        target=reminder_loop,
        daemon=True
    ).start()


    print("提醒排程已啟動")


    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        )
    )