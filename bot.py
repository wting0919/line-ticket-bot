from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from datetime import datetime, timedelta
import json
import os


app = Flask(__name__)

import os
from dotenv import load_dotenv

load_dotenv()

CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
USER_ID = os.getenv("USER_ID")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


DATA_FILE = "shows.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return []

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    handler.handle(body, signature)

    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    text = event.message.text.strip()


    # 查詢功能
    if text == "查詢":

        shows = load_data()

        if not shows:
            reply = "目前沒有演出資料"

        else:
            reply = "🎫 目前演出：\n\n"

            for s in shows:
                reply += (
                    f"🎤 {s['演出名稱']}\n"
                    f"📅 演出：{s['演出日期']}\n"
                    f"📦 取票提醒：{s['取票日期']}\n"
                    f"🎟 搶票：{s['搶票日期']}\n\n"
                )


    # 新增功能
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


            ticket_date = (
                event_date - timedelta(days=5)
            ).strftime("%Y/%m/%d")


            show = {
                "演出名稱": data.get("演出名稱", ""),
                "演出日期": data.get("演出日期", ""),
                "搶票日期": data.get("搶票日期", ""),
                "價錢&張數": data.get("價錢&張數", ""),
                "搶票網站": data.get("搶票網站", ""),
                "取票日期": ticket_date,
                "備註": data.get("備註", "")
            }


            shows = load_data()
            shows.append(show)
            save_data(shows)


            reply = (
                "✅ 新增成功\n\n"
                f"🎤 {show['演出名稱']}\n"
                f"📅 演出日期：{show['演出日期']}\n"
                f"🎫 取票提醒：{show['取票日期']}\n"
                f"🎟 搶票日期：{show['搶票日期']}\n"
                f"💰 {show['價錢&張數']}\n"
                f"🌐 {show['搶票網站']}\n"
                f"📝 {show['備註']}"
            )


        except Exception as e:
            reply = (
                "❌ 格式錯誤\n"
                "請照格式輸入\n\n"
                "新增\n"
                "演出名稱：XXX\n"
                "演出日期：2026/08/20"
            )


    elif text == "ID":
        reply = event.source.user_id


    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )


import os

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )