from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from datetime import datetime, timedelta
import json
import os
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv


app = Flask(__name__)


load_dotenv()


CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
USER_ID = os.getenv("USER_ID")
GROUP_ID = os.getenv("GROUP_ID")


scheduler = BackgroundScheduler()


line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


DATA_FILE = "shows.json"


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



def sort_shows(shows):

    return sorted(
        shows,
        key=lambda x: datetime.strptime(
            x["搶票時間"],
            "%Y/%m/%d %H:%M"
        )
    )



# =====================
# 提醒功能
# =====================

def check_reminders():

    print("提醒檢查執行", datetime.now())

    now = datetime.now()

    shows = load_data()

    for show in shows:

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


            if now.strftime("%Y/%m/%d %H:%M") == remind_time.strftime("%Y/%m/%d %H:%M"):

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


            diff = ticket_time - now


            # 前30分鐘

            if (
                timedelta(minutes=29)
                < diff <= timedelta(minutes=30)
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


            # 前10分鐘

            if (
                timedelta(minutes=9)
                < diff <= timedelta(minutes=10)
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


        except Exception as e:

            print(
                f"提醒錯誤：{e}"
            )


        # 取票提醒

        if today == show.get("取票日期"):

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
    # 列表功能
    # =====================

    elif text == "列表":


        shows = sort_shows(
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
                    f"🎟 搶票時間：{show['搶票時間']}\n"
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
                    data.get("備註", "")
            }



            shows = load_data()

            shows.append(show)

            save_data(shows)



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

        shows = sort_shows(
            load_data()
        )


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


        shows = sort_shows(
            load_data()
        )


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
    # 刪除功能
    # =====================

    elif text.startswith("刪除"):


        shows = sort_shows(
            load_data()
        )


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


    scheduler.add_job(
        check_reminders,
        "interval",
        seconds=10,
        id="check_reminders",
        replace_existing=True
    )


    scheduler.start()


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