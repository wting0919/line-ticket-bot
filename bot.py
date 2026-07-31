# Python
import os
import linebot

# Flask
from flask import Flask, request

# LINE
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
)

# Scheduler
from apscheduler.schedulers.background import BackgroundScheduler

# Modules
import add_show
import complete_ticket
import delete_show
import edit_show
import member
import mention
import pickup
import reminder
import serial
import view_show
import copy_show
import search_show

# Data
from reminder import (
    check_reminders,
    clean_finished_shows,
    send_today_summary,
)

from show_list import (
    get_all_shows,
    get_pickup_shows,
    get_waiting_shows,
)

from ui import (
    menu_reply,
)

from utils import (
    format_datetime,
    format_show_dates,
)

# Handlers
from add_show import (
    start_add_show,
    handle_add_show_flow,
)

from complete_ticket import (
    handle_complete_ticket,
    handle_complete_ticket_flow,
    handle_ticket_failed,
)

from delete_show import (
    handle_delete_show,
)

from edit_show import (
    start_edit_show,
    handle_edit_show_flow,
)

from copy_show import handle_copy_show

from search_show import (
    handle_search_show,
)

from next_show import (
    handle_next_show,
)

from prev_show import (
    handle_prev_show,
)

from member import (
    handle_register_member,
)

from pickup import (
    handle_complete_pickup,
)

from serial import (
    handle_serial_number,
)

from view_show import (
    handle_view_show,
)



app = Flask(__name__)


CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
GROUP_ID = os.getenv("GROUP_ID")


line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


scheduler = BackgroundScheduler(
    timezone="Asia/Taipei",
    job_defaults={
        "coalesce": False,
        "max_instances": 3,
        "misfire_grace_time": 120
    }
)


# 使用者操作狀態
user_state = {}

# =====================
# 初始化模組
# =====================

add_show.line_bot_api = line_bot_api
add_show.user_state = user_state

edit_show.line_bot_api = line_bot_api
edit_show.user_state = user_state

copy_show.line_bot_api = line_bot_api
copy_show.user_state = user_state

search_show.line_bot_api = line_bot_api
search_show.user_state = user_state

complete_ticket.line_bot_api = line_bot_api
complete_ticket.user_state = user_state

view_show.line_bot_api = line_bot_api
view_show.user_state = user_state

pickup.line_bot_api = line_bot_api

delete_show.line_bot_api = line_bot_api
delete_show.user_state = user_state

member.line_bot_api = line_bot_api

serial.line_bot_api = line_bot_api
serial.GROUP_ID = GROUP_ID

mention.CHANNEL_ACCESS_TOKEN = CHANNEL_ACCESS_TOKEN

reminder.line_bot_api = line_bot_api
reminder.GROUP_ID = GROUP_ID
reminder.push_mention_message = mention.push_mention_message

# =====================
# LINE Callback
# =====================

@app.route("/health", methods=["GET"])
def health():

    return "OK", 200



@app.route("/callback", methods=["POST"])
def callback():

    signature = request.headers["X-Line-Signature"]

    body = request.get_data(as_text=True)


    handler.handle(
        body,
        signature
    )


    return "OK"



@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    print(event.source)

    text = event.message.text.strip()

    user_id = event.source.user_id


    # =====================
    # 問答式流程處理
    # =====================

    if handle_complete_ticket_flow(
        event,
        text,
        user_id
    ):
        return

    if handle_add_show_flow(
        event,
        text,
        user_id
    ):
        return

    if handle_edit_show_flow(
        event,
        text,
        user_id
    ):
        return

    # =====================
    # 選單
    # =====================

    if text in (
        "選單",
        "menu",
        "Menu",
        "MENU",
        "help",
        "Help",
        "HELP"
    ):

        line_bot_api.reply_message(
            event.reply_token,
            menu_reply(
                "📋 演唱會小助手\n\n"
                "請點選下方快捷按鈕 👇"
            )
        )
        return


    # =====================
    # 測試提醒
    # =====================

    elif text == "測試提醒":


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
                    f"🎟 {format_datetime(show.get('搶票時間'))}\n"
                    f"🌐 售票平台：{show['售票平台']}\n"
                    f"📝 備註：{show['備註'] if show['備註'] else '無'}\n"
                    f"📌 狀態：{show.get('搶票狀態','等待搶票')}\n"
                )


            reply += (
                "\n👉 查看詳細資料：\n"
                "輸入：查看 1"
            )

            user_state[user_id] = {
                "mode": "搶票列表",
                "shows": waiting,
                "current_index": None,
            }


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
                    f"🎟 搶票大師：{show.get('搶票大師', '未設定')}\n"
                    f"👥 取票人：{show.get('取票人') or '未設定'}\n"
                    f"📌 狀態：{show.get('取票狀態','未取票')}\n"
                )


            user_state[user_id] = {
                "mode": "取票列表",
                "shows": pickup_list,
                "current_index": None,
            }


    # =====================
    # 演出列表功能
    # =====================

    elif text == "演出列表":


        shows = get_all_shows()


        if not shows:

            reply = "目前沒有演出資料"


        else:

            reply = "🎫 演出列表\n"


            for i, show in enumerate(
                shows,
                start=1
            ):

                status = show.get("搶票狀態", "等待搶票")

                ticket_status = {
                    "已搶票": "✅ 已搶票",
                    "未搶到": "❌ 未搶到",
                }.get(
                    status,
                    "⏳ 等待搶票"
                )

                pickup_status = ""

                if status == "已搶票":

                    pickup_status = (
                        "✅ 已取票"
                        if show.get("取票狀態") == "已取票"
                        else "🎫 未取票"
                    )

                reply += (
                    f"\n{i}.\n"
                    f"🎤 {show['演出名稱']}\n"
                    f"📅 {format_show_dates(show['演出日期'])}\n"
                    f"{ticket_status}"
                )

                if pickup_status:
                    reply += f"\n{pickup_status}"

                reply += "\n"


            reply += (
                "\n👉 查看詳細資料：\n"
                "輸入：查看 1"
            )

            user_state[user_id] = {
                "mode": "演出列表",
                "shows": shows,
                "current_index": None,
            }


    elif text == "上一筆":

        handle_prev_show(
            event,
            user_id,
        )
        return

    elif text == "下一筆":

        handle_next_show(
            event,
            user_id,
        )
        return


    # =====================
    # 新增功能
    # =====================

    elif text in ("新增", "新增演出"):

        start_add_show(
            event,
            user_id
        )

        return


    # =====================
    # 查看功能
    # =====================

    elif text.startswith("查看"):

        handle_view_show(
            event,
            text,
            user_id,
        )

        return

    # =====================
    # 搜尋功能
    # =====================

    elif text.startswith("搜尋"):

        handle_search_show(
            event,
            text,
            user_id
        )

        return


    # =====================
    # 修改功能
    # =====================

    elif text.startswith("修改"):

        start_edit_show(
            event,
            text,
            user_id
        )

        return

    # =====================
    # 複製功能
    # =====================

    elif text.startswith("複製"):

        handle_copy_show(event, text, user_id)

        return

    # =====================
    # 完成搶票
    # =====================

    elif text.startswith("完成搶票"):

        message = handle_complete_ticket(
            event,
            text,
            user_id
        )

        line_bot_api.reply_message(
            event.reply_token,
            message
        )

        return

    # =====================
    # 未搶到
    # =====================

    elif text.startswith("未搶到"):

        message = handle_ticket_failed(
            event,
            text,
            user_id
        )

        line_bot_api.reply_message(
            event.reply_token,
            message
        )

        return


    # =====================
    # 序號提醒
    # =====================

    elif text.startswith("序號"):

        handle_serial_number(
            event,
            text,
        )

        return

    # =====================
    # 完成取票
    # =====================

    elif text.startswith("完成取票"):

        handle_complete_pickup(
            event,
            text,
            user_id,
        )

        return


    # =====================
    # 刪除功能
    # =====================

    elif text.startswith("刪除"):

        handle_delete_show(
            event,
            text,
            user_id,
        )

        return


    # =====================
    # 幫助
    # =====================

    elif text == "幫助":

        reply = (
            "📖 功能選單\n\n"
            "🎟 搶票列表\n"
            "🎫 取票列表\n"
            "📅 演出列表\n"
            "🔍 搜尋 SEVENTEEN\n\n"
            "🔍 查看 1\n"
            "✏️ 修改 1\n"
            "📄 複製 1\n"
            "🗑 刪除 1\n"
            "✅ 完成搶票 1\n"
            "🎫 完成取票 1\n\n"
            "💡 輸入「選單」可再次開啟快捷按鈕。"
        )


    # =====================
    # 登記暱稱
    # =====================

    elif text.startswith("登記"):

        handle_register_member(
            event,
            text,
            user_id,
        )
        return

    else:

        return

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

print("LINE SDK Version:", getattr(linebot, "__version__", "Unknown"))

if __name__ == "__main__":


    scheduler.add_job(
        check_reminders,
        "interval",
        minutes=1,
        id="check_reminders",
        replace_existing=True
    )


    scheduler.add_job(
        clean_finished_shows,
        "cron",
        hour=3,
        minute=0,
        id="clean_finished_shows",
        replace_existing=True
    )


    scheduler.add_job(
        send_today_summary,
        "cron",
        hour=9,
        minute=0,
        id="send_today_summary",
        replace_existing=True
    )


    scheduler.start()


    print("提醒排程已啟動")


    print(
        "目前排程：",
        scheduler.get_jobs()
    )

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        )
    )
