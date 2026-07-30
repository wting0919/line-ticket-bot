import add_show
import edit_show
import complete_ticket
import mention
import reminder

from utils import (
    format_price,

    parse_date,
    split_show_dates,
    format_show_dates,
    get_first_show_date,
    get_last_show_date,
    normalize_show_date,

    parse_datetime,
    format_datetime,
    normalize_ticket_time,
    normalize_pickup_date,

    sort_shows,
    sort_by_show_date,
    sort_by_pickup_date,
)

from data import (
    supabase,
    load_data,
    save_data,
    update_show,
    get_user_id,
    get_member,
    load_members,
    get_member_user_id,
)

from ui import (
    menu_reply,
    member_quick_reply,
    simple_quick_reply,
    edit_field_quick_reply,
)

from mention import (
    push_mention_message,
)

from reminder import (
    check_reminders,
    clean_finished_shows,
)

import linebot

from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
)

from datetime import datetime, timedelta
import json
import os
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)


CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
mention.CHANNEL_ACCESS_TOKEN = CHANNEL_ACCESS_TOKEN
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
USER_ID = os.getenv("USER_ID")
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

# add_show 不依賴任何函式
add_show.line_bot_api = line_bot_api
add_show.user_state = user_state

from add_show import (
    start_add_show,
    handle_add_show_flow,
)

from edit_show import (
    start_edit_show,
    handle_edit_show_flow,
)

from complete_ticket import (
    handle_complete_ticket,
    handle_complete_ticket_flow,
)

# =====================
# 資料處理
# =====================




def load_users():

    if not os.path.exists(USER_FILE):
        return {}

    with open(USER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)



def save_users(users):

    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(
            users,
            f,
            ensure_ascii=False,
            indent=4
        )


def format_date(value):

    dt = parse_date(value)

    if dt == datetime.max:
        return value

    return dt.strftime("%Y/%m/%d")
  
# =====================
# 共用列表功能
# =====================

def get_waiting_shows():

    shows = sort_shows(load_data())

    waiting = []

    for show in shows:

        show.setdefault(
            "搶票狀態",
            "等待搶票"
        )

        if show["搶票狀態"] == "等待搶票":

            try:

                ticket_time = parse_datetime(
                    show["搶票時間"]
                )


                now = datetime.now() + timedelta(hours=8)

                if ticket_time > now:
                    waiting.append(show)


            except Exception as e:

                print(
                    "搶票時間錯誤：",
                    e
                )


    return waiting



def get_pickup_shows():

    shows = sort_by_pickup_date(load_data())

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

    shows = sort_by_show_date(load_data())

    print("演出列表讀取：", shows)

    return shows

edit_show.line_bot_api = line_bot_api
edit_show.user_state = user_state
edit_show.get_waiting_shows = get_waiting_shows
edit_show.get_pickup_shows = get_pickup_shows
edit_show.get_all_shows = get_all_shows

complete_ticket.line_bot_api = line_bot_api
complete_ticket.user_state = user_state
complete_ticket.get_all_shows = get_all_shows

reminder.line_bot_api = line_bot_api
reminder.GROUP_ID = GROUP_ID
reminder.push_mention_message = push_mention_message


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

    show_menu = False

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

    if text in [
        "選單",
        "menu",
        "Menu",
        "MENU",
        "help",
        "Help",
        "HELP"
    ]:

        show_menu = True

        reply = (
            "📋 演唱會小助手\n\n"
            "請點選下方快捷按鈕 👇"
        )


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

            user_state[user_id] = "搶票列表"


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


            user_state[user_id] = "取票列表"


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

                ticket_status = (
                    "✅ 已搶票"
                    if show.get("搶票狀態") == "已搶票"
                    else "⏳ 等待搶票"
                )

                pickup_status = (
                    "✅ 已取票"
                    if show.get("取票狀態") == "已取票"
                    else "⏳ 未取票"
                )

                reply += (
                    f"\n{i}.\n"
                    f"🎤 {show['演出名稱']}\n"
                    f"📅 演出日期：\n{format_show_dates(show['演出日期'])}\n"
                    f"🎟 {ticket_status}\n"
                    f"🎫 {pickup_status}\n"
                )


            reply += (
                "\n👉 查看詳細資料：\n"
                "輸入：查看 1"
            )

            user_state[user_id] = "演出列表"

    # =====================
    # 新增功能
    # =====================

    elif text in ["新增", "新增演出"]:

        start_add_show(
            event,
            user_id
        )

        return


    # =====================
    # 查看功能
    # =====================

    elif text.startswith("查看"):


        if user_state.get(user_id) == "搶票列表":

            shows = get_waiting_shows()


        elif user_state.get(user_id) == "取票列表":

            shows = get_pickup_shows()


        else:

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
                    f"{format_show_dates(show['演出日期'])}\n\n"

                    "🎟 搶票時間\n"
                    f"{format_datetime(show['搶票時間'])}\n\n"

                    "💰 價格張數\n"
                    f"{format_price(show['價格張數'])}\n\n"

                    "🌐 售票平台\n"
                    f"{show['售票平台']}\n\n"

                    "📌 搶票狀態\n"
                    f"{show.get('搶票狀態','等待搶票')}\n\n"

                    "🎫 取票狀態\n"
                    f"{show.get('取票狀態','未取票')}\n\n"

                    "🎟 搶票大師\n"
                    f"{show.get('搶票大師', '未設定')}\n\n"

                    "👥 取票人\n"
                    f"{show.get('取票人') or '未設定'}\n\n"

                    "📝 備註\n"
                    f"{note}"
                )


        except ValueError:

            reply = "請輸入格式：\n查看 1"

        except Exception as e:

            print("查看錯誤：", e)

            reply = f"❌ 發生錯誤\n{e}"



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
    # 序號提醒
    # =====================

    elif text.startswith("序號"):

        shows = get_all_shows()


        try:

            lines = text.split("\n")


            index = int(
                lines[0]
                .replace(
                    "序號",
                    ""
                )
                .strip()
            ) - 1


            if index < 0 or index >= len(shows):

                reply = "❌ 找不到這筆演出"


            else:

                show = shows[index]


                for line in lines[1:]:

                    if line.startswith("取票序號："):

                        show["取票序號"] = (
                            line
                            .replace(
                                "取票序號：",
                                ""
                            )
                            .strip()
                        )


                update_show(show)


                reply = (
                    "🎫 序號已出來！\n\n"
                    f"🎤 {show['演出名稱']}\n\n"
                    f"🎟 序號：\n"
                    f"{show.get('取票序號','')}\n\n"
                    f"👤 搶票大師：\n"
                    f"{show.get('搶票大師','未設定')}\n\n"
                    f"👥 取票人：\n"
                    f"{show.get('取票人') or '未設定'}\n\n"
                    "請確認取票資訊～"
                )


                mention_names = []

                if show.get("搶票大師"):
                    mention_names.append(show["搶票大師"])

                mention_names.extend(
                    [
                        x.strip()
                        for x in show.get("取票人", "").split("、")
                        if x.strip()
                    ]
                )

                push_mention_message(
                    GROUP_ID,
                    reply,
                    mention_names
                )


                reply = "✅ 已發送序號提醒"


        except Exception as e:

            print(e)

            reply = (
                "請輸入格式：\n"
                "序號 1\n"
                "取票序號：A123456"
            )


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

                    if show["id"] == target["id"]:

                        show["取票狀態"] = "已取票"

                        update_show(show)

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


        try:

            index = int(
                text.replace(
                    "刪除",
                    ""
                ).strip()
            ) - 1


            if user_state.get(user_id) == "搶票列表":

                target_list = get_waiting_shows()

            elif user_state.get(user_id) == "取票列表":

                target_list = get_pickup_shows()

            else:

                target_list = get_all_shows()



            target = target_list[index]


            deleted = target


            supabase.table("shows") \
                .delete() \
                .eq(
                    "id",
                    target["id"]
                ) \
                .execute()


            reply = (
                "✅ 刪除成功\n\n"
                f"🎤 {deleted['演出名稱']}\n"
                f"📅 演出日期：{deleted['演出日期']}"
            )


        except Exception as e:

            print(e)

            reply = "請輸入格式：\n刪除 1"


    # =====================
    # 幫助
    # =====================

    elif text == "幫助":

        reply = (
            "📖 功能選單\n\n"
            "🎟 搶票列表\n"
            "🎫 取票列表\n"
            "📅 演出列表\n\n"
            "🔍 查看 1\n"
            "✏️ 修改 1\n"
            "✅ 完成搶票 1\n"
            "🎫 完成取票 1\n"
            "🗑 刪除 1\n\n"
            "💡 輸入「選單」可再次開啟快捷按鈕。"
        )


    # =====================
    # 登記暱稱
    # =====================

    elif text.startswith("登記 "):

        nickname = text.replace(
            "登記 ",
            ""
        ).strip()


        if not nickname:

            reply = "請輸入：登記 暱稱"


        else:

            supabase.table("members").upsert(
                {
                    "name": nickname,
                    "user_id": user_id
                },
                on_conflict="user_id"
            ).execute()


            reply = (
                "✅ 登記成功\n\n"
                f"暱稱：{nickname}\n"
                f"ID：{user_id}"
            )

    else:

        return



    if show_menu:

        line_bot_api.reply_message(
            event.reply_token,
            menu_reply(reply)
        )

    else:

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
