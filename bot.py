import linebot

from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
    QuickReply,
    QuickReplyButton,
    MessageAction
)

from datetime import datetime, timedelta
import json
import os
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from supabase import create_client


app = Flask(__name__)


load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
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


DATA_FILE = "./shows.json"
USER_FILE = "./users.json"


# 使用者操作狀態
user_state = {}



# =====================
# 資料處理
# =====================

def load_data():

    response = (
        supabase
        .table("shows")
        .select("*")
        .execute()
    )

    shows = response.data

    return shows

def save_data(data):

    try:

        if data:

            supabase.table("shows").upsert(
                data
            ).execute()


        print("Supabase儲存完成")


    except Exception as e:

        print("Supabase儲存錯誤：", e)


def update_show(show):

    show_id = show["id"]

    data = show.copy()
    data.pop("id")

    supabase.table("shows") \
        .update(data) \
        .eq("id", show_id) \
        .execute()


def load_members():

    if not os.path.exists("members.json"):
        return {}

    with open("members.json", "r", encoding="utf-8") as f:
        return json.load(f)



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

def parse_datetime(value):

    if not value:
        return datetime.max

    try:

        # Supabase ISO 格式
        if "T" in value:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            ).replace(tzinfo=None)


        # 2026-08-17 12:00
        if "-" in value:
            return datetime.strptime(
                value,
                "%Y-%m-%d %H:%M"
            )


        # 2026/08/17 12:00
        return datetime.strptime(
            value,
            "%Y/%m/%d %H:%M"
        )


    except Exception as e:

        print("時間解析錯誤：", value, e)

        return datetime.max


def parse_date(value):

    if not value:
        return datetime.max

    try:

        # Supabase ISO
        if "T" in value:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            ).replace(tzinfo=None)


        # 2026-08-17
        if "-" in value:
            return datetime.strptime(
                value,
                "%Y-%m-%d"
            )


        # 2026/08/17
        return datetime.strptime(
            value,
            "%Y/%m/%d"
        )


    except Exception as e:

        print("日期解析錯誤：", value, e)

        return datetime.max

def format_datetime(value):

    dt = parse_datetime(value)

    if dt == datetime.max:
        return value

    return dt.strftime("%Y/%m/%d %H:%M")


def format_date(value):

    dt = parse_date(value)

    if dt == datetime.max:
        return value

    return dt.strftime("%Y/%m/%d")


# =====================
# 排序功能
# =====================

def sort_shows(shows):
    # 搶票時間排序

    return sorted(
        shows,
        key=lambda x: parse_datetime(
            x.get("搶票時間")
        )
    )



def sort_by_show_date(shows):
    # 演出日期排序

    return sorted(
        shows,
        key=lambda x: parse_date(
            x.get("演出日期")
        )
    )



def sort_by_pickup_date(shows):
    # 取票日期排序

    return sorted(
        shows,
        key=lambda x: parse_date(
            x.get("取票日期")
        )
    )
    
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

# =====================
# 提醒功能
# =====================

def check_reminders():

    print("提醒檢查執行", datetime.now())

    now = datetime.now() + timedelta(hours=8)

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

        print(
            "提醒狀態：",
            show["演出名稱"],
            show["提醒"]
        )


        show.setdefault("搶票狀態", "等待搶票")
        show.setdefault("取票狀態", "未取票")


        try:

            ticket_time = parse_datetime(
                show["搶票時間"]
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
                            f"🎟 搶票時間：{format_datetime(show['搶票時間'])}\n"
                            f"🌐 售票平台：{show['售票平台']}"
                        )
                    )
                )


                show["提醒"]["前一天"] = True
                save_data(shows)


            diff = ticket_time - now

            print("=" * 50)
            print("現在時間：", now)
            print("演出：", show["演出名稱"])
            print("搶票時間：", ticket_time)
            print("剩餘：", diff)
            print("30分鐘：", show["提醒"]["30分鐘"])
            print("10分鐘：", show["提醒"]["10分鐘"])


            # 前30分鐘

            if (
                timedelta(minutes=29)
                <= diff 
                <= timedelta(minutes=30)
                and not show["提醒"]["30分鐘"]
            ):


                print(">>> 發送30分鐘提醒")


                line_bot_api.push_message(
                    GROUP_ID,
                    TextSendMessage(
                        text=(
                            "⏰ 搶票倒數 30 分鐘\n\n"
                            f"🎤 {show['演出名稱']}\n"
                            f"🎟 搶票時間：{format_datetime(show['搶票時間'])}\n"
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
                <= diff 
                <= timedelta(minutes=10)
                and not show["提醒"]["10分鐘"]
            ):

                print(">>> 發送10分鐘提醒")


                line_bot_api.push_message(
                    GROUP_ID,
                    TextSendMessage(
                        text=(
                            "🔐 搶票倒數 10 分鐘\n\n"
                            f"🎤 {show['演出名稱']}\n"
                            f"🎟 搶票時間：{format_datetime(show['搶票時間'])}\n"
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

            pickup_time = parse_datetime(
                show["取票日期"] + " 12:00"
            )

            if (
                pickup_time <= now < pickup_time + timedelta(minutes=1)
                and not show["提醒"]["取票"]
            ):

                participants = show.get("參加者", [])


                mention_text = "".join(
                    f"@{name}\n"
                    for name in participants
                )

                line_bot_api.push_message(
                    GROUP_ID,
                    TextSendMessage(
                        text=(
                            "🎫 取票提醒\n\n"
                            f"🎤 {show['演出名稱']}\n\n"
                            f"{mention_text}"
                            "🎫可以取票囉~"
                        )
                    )
                )

                show["提醒"]["取票"] = True
                save_data(shows)

def clean_finished_shows():

    print("檢查過期演出")

    now = datetime.now() + timedelta(hours=8)

    shows = load_data()

    keep_shows = []

    for show in shows:

        try:

            show_date = parse_date(
                show.get("演出日期")
            )

            # 演出日 + 3天
            delete_date = (
                show_date +
                timedelta(days=3)
            )

            if now.date() <= delete_date.date():

                keep_shows.append(show)

            else:

                print(
                    "刪除已結束演出：",
                    show.get("演出名稱")
                )


        except Exception as e:

            print(
                "清除錯誤：",
                e
            )

            keep_shows.append(show)


    if len(keep_shows) != len(shows):

        # 刪除 Supabase 資料
        old_ids = [
            show["id"]
            for show in shows
            if show not in keep_shows
        ]

        for show_id in old_ids:

            supabase.table("shows") \
                .delete() \
                .eq("id", show_id) \
                .execute()


    print("清除完成")


def menu_reply(text):

    return TextSendMessage(
        text=text,
        quick_reply=QuickReply(
            items=[

                
                QuickReplyButton(
                    action=MessageAction(
                        label="➕ 新增演出",
                        text="新增演出"
                    )
                ),

                QuickReplyButton(
                    action=MessageAction(
                        label="🎟 搶票列表",
                        text="搶票列表"
                    )
                ),

                QuickReplyButton(
                    action=MessageAction(
                        label="🎫 取票列表",
                        text="取票列表"
                    )
                ),

                QuickReplyButton(
                    action=MessageAction(
                        label="📅 演出列表",
                        text="演出列表"
                    )
                ),

                QuickReplyButton(
                    action=MessageAction(
                        label="❓ 幫助",
                        text="幫助"
                    )
                ),

                QuickReplyButton(
                    action=MessageAction(
                        label="🆔 我的ID",
                        text="ID"
                    )
                ),

            ]
        )
    )

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



# =====================
# 訊息處理
# =====================

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print(event.source)

    text = event.message.text.strip()

    user_id = event.source.user_id

    show_menu = False


    # =====================
    # 選單
    # =====================

    if text in ["選單", "menu", "Menu", "MENU", "help", "Help", "HELP"]:

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

            user_state[user_id] = "演出列表"

    # =====================
    # 新增功能
    # =====================
   

    elif text == "取消新增":
        user_state.pop(user_id, None)
        reply = "已取消新增"



    elif text in ["新增", "新增演出"]:
        
        user_state[user_id] = "新增模式"

        reply = (
            "➕ 新增演出模式\n\n"
            "請複製以下格式填寫：\n\n"
            "演出名稱：XXX演唱會\n"
            "演出日期：10/1\n"
            "搶票時間：9/1 12:00\n"
            "價格張數：$3800*2\n"
            "售票平台：拓元\n"
            "取票日期：5天前\n"
            "備註：會員預售/XX卡友優先購\n\n"
            "輸入「取消新增」可取消"
        )


    elif (
        (text.startswith("新增\n"))
        or user_state.get(user_id) == "新增模式"
    ):


        if user_state.get(user_id) == "新增模式":

            text = "新增\n" + text



        try:

            lines = text.split("\n")

            data = {}


            for line in lines:

                if "：" in line:

                    key, value = line.split("：", 1)

                    data[key.strip()] = value.strip()



            event_date_text = data["演出日期"]


            # 支援 8/23 自動補年份
            if "/" in event_date_text and event_date_text.count("/") == 1:

                year = datetime.now().year

                event_date_text = (
                    f"{year}/{event_date_text}"
                )


            event_date = datetime.strptime(
                event_date_text,
                "%Y/%m/%d"
            )


            data["演出日期"] = event_date.strftime(
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

            ticket_time_text = data.get(
                "搶票時間",
                ""
            )


            # 支援 5/1 12:00 自動補年份
            if "/" in ticket_time_text:

                date_part, time_part = ticket_time_text.split(
                    " ",
                    1
                )

                if date_part.count("/") == 1:

                    year = datetime.now().year

                    ticket_time_text = (
                        f"{year}/{date_part} {time_part}"
                    )


            ticket_datetime = datetime.strptime(
                ticket_time_text,
                "%Y/%m/%d %H:%M"
            )

            data["搶票時間"] = ticket_datetime.strftime(
                "%Y/%m/%d %H:%M"
            )





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



            print("準備寫入 Supabase：", show)

            supabase.table("shows").insert(show).execute()

            user_state.pop(user_id, None)

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

            print("新增錯誤詳細：", repr(e))

            reply = f"❌ 新增錯誤\n{e}"



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
                    f"{show['演出日期']}\n\n"

                    "🎟 搶票時間\n"
                    f"{format_datetime(show['搶票時間'])}\n\n"

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


        if user_state.get(user_id) == "搶票列表":

            shows = get_waiting_shows()


        elif user_state.get(user_id) == "取票列表":

            shows = get_pickup_shows()


        else:

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



                update_show(show)


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

                   
                update_show(show)


                reply = (
                    "✅ 已完成搶票\n\n"
                    f"🎤 {show['演出名稱']}\n"
                    f"🎟 搶票大師：{show['搶票大師']}\n"
                    f"👥 參加者：{'、'.join(show.get('參加者', [])) if show.get('參加者') else '無'}\n"
                    "📌 狀態：已搶票"
                )


        except Exception as e:

            import traceback
            traceback.print_exc()

            reply = f"❌ 完成搶票錯誤\n{e}"

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


                save_data(shows)


                reply = (
                    "🎫 序號已出來！\n\n"
                    f"🎤 {show['演出名稱']}\n\n"
                    f"🎟 序號：\n"
                    f"{show.get('取票序號','')}\n\n"
                    f"👤 搶票大師：\n"
                    f"{show.get('搶票大師','未設定')}\n\n"
                    f"👥 參加者：\n"
                    f"{'、'.join(show.get('參加者',[]))}\n\n"
                    "請確認取票資訊～"
                )


                line_bot_api.push_message(
                    GROUP_ID,
                    TextSendMessage(
                        text=reply
                    )
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

                    if (
                        show.get("演出名稱") == target.get("演出名稱")
                        and show.get("演出日期") == target.get("演出日期")
                    ):

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

            users = load_users()

            users[nickname] = user_id

            save_users(users)


            reply = (
                "✅ 登記成功\n\n"
                f"暱稱：{nickname}\n"
                f"ID：{user_id}"
            )


    # =====================
    # ID
    # =====================

    elif text == "ID":


        if event.source.type == "group":

            reply = event.source.group_id

        else:

            reply = event.source.user_id



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
        clean_finished_shows,
        "cron",
        hour=3,
        minute=0
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
