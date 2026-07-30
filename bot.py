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
import requests
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


def get_user_id(name):
    result = (
        supabase
        .table("members")
        .select("user_id")
        .eq("name", name)
        .execute()
    )

    if result.data:
        return result.data[0]["user_id"]

    return None


def get_member(name):
    result = (
        supabase
        .table("members")
        .select("*")
        .eq("name", name)
        .execute()
    )

    if result.data:
        return result.data[0]

    return None


def load_members():

    try:
        response = (
            supabase
            .table("members")
            .select("*")
            .execute()
        )

        return {
            row["name"].strip(): row["user_id"].strip()
            for row in response.data
            if row.get("name") and row.get("user_id")
        }

    except Exception as e:
        print("讀取 members 錯誤：", e)
        return {}


def get_member_user_id(name):

    if not name:
        return None

    members = load_members()
    return members.get(name.strip())


def push_mention_message(to, message_text, names):
    """使用 LINE textV2 傳送真正的 @ 提及。

    找不到 members.user_id 的名字會保留為普通文字，
    讓整則提醒不會因單一成員資料缺漏而失敗。
    """

    names = [
        str(name).strip()
        for name in (names or [])
        if str(name).strip()
    ]

    substitution = {}
    mention_lines = []
    missing_names = []

    # LINE 單則訊息最多可替換 20 個 mention。
    for index, name in enumerate(names[:20]):
        user_id = get_member_user_id(name)

        if user_id:
            key = f"mention{index}"
            mention_lines.append(f"{{{key}}}")
            substitution[key] = {
                "type": "mention",
                "mentionee": {
                    "type": "user",
                    "userId": user_id
                }
            }
        else:
            mention_lines.append(f"@{name}")
            missing_names.append(name)

    final_text = message_text

    if mention_lines:
        final_text += "\n\n" + "\n".join(mention_lines)

    payload = {
        "to": to,
        "messages": [
            {
                "type": "textV2",
                "text": final_text,
                "substitution": substitution
            }
        ]
    }

    # 沒有真正 mention 時，substitution 不需要送出。
    if not substitution:
        payload["messages"][0].pop("substitution", None)

    response = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers={
            "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=15
    )

    if not response.ok:
        raise RuntimeError(
            f"LINE mention 發送失敗：{response.status_code} {response.text}"
        )

    if missing_names:
        print("以下成員找不到 user_id，改用普通文字：", missing_names)

    return True



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

WEEKDAY = ["一", "二", "三", "四", "五", "六", "日"]

def format_show_dates(value):

    if not value:
        return ""

    result = []

    for d in split_show_dates(value):

        dt = parse_date(d)

        result.append(
            f"{dt.strftime('%Y/%m/%d')}（{WEEKDAY[dt.weekday()]}）"
        )

    return "\n".join(result)

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
        key=lambda show: parse_date(
            get_first_show_date(show)
        )
    )


def sort_by_pickup_date(shows):
    # 取票日期排序

    return sorted(
        shows,
        key=lambda x: (
            parse_datetime(x.get("搶票時間")),
            parse_date(x.get("演出日期")),
            str(x.get("id", ""))
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
                update_show(show)


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
                update_show(show)


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
                update_show(show)


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

                participants = [
                    x.strip()
                    for x in show.get("取票人", "").split("、")
                    if x.strip()
                ]

                push_mention_message(
                    GROUP_ID,
                    (
                        "🎫 取票提醒\n\n"
                        f"🎤 {show['演出名稱']}\n"
                        "🎫 可以取票囉～"
                    ),
                    participants
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
                    f"🗑️ 已自動清除：{show['演出名稱']}"
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

            try:

                supabase.table("shows") \
                    .delete() \
                    .eq("id", show_id) \
                    .execute()

                print(f"已刪除：{show_id}")

            except Exception as e:

                print(f"刪除失敗：{show_id}", e)
        

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


            ]
        )
    )

def member_quick_reply(
    selected=None,
    allow_finish=False,
    allow_skip=True
):

    selected = selected or []

    members = load_members()

    print(
        "Quick Reply 讀到的成員：",
        members,
        flush=True
    )

    items = []

    for name in members.keys():

        if name in selected:
            continue

        items.append(
            QuickReplyButton(
                action=MessageAction(
                    label=f"👤 {name}",
                    text=name
                )
            )
        )

    if allow_finish:

        items.append(
            QuickReplyButton(
                action=MessageAction(
                    label="✅ 完成",
                    text="完成"
                )
            )
        )

    if allow_skip:

        items.append(
            QuickReplyButton(
                action=MessageAction(
                    label="➖ 略過",
                    text="略過"
                )
            )
        )

    items.append(
        QuickReplyButton(
            action=MessageAction(
                label="❌ 取消",
                text="取消"
            )
        )
    )

    return QuickReply(items=items)


def simple_quick_reply(buttons):

    items = []

    for label, value in buttons:

        items.append(
            QuickReplyButton(
                action=MessageAction(
                    label=label,
                    text=value
                )
            )
        )

    return QuickReply(items=items)

def split_show_dates(value):

    value = value.strip().replace("，", "、").replace("-", "/")

    # 10/10~10/12
    if "~" in value:

        start, end = value.split("~")

        start = normalize_show_date(start)
        end = normalize_show_date(end)

        start_date = parse_date(start)
        end_date = parse_date(end)

        result = []

        while start_date <= end_date:

            result.append(
                start_date.strftime("%Y/%m/%d")
            )

            start_date += timedelta(days=1)

        return result

    result = []

    year = datetime.now().year
    last_month = None

    for item in value.split("、"):

        item = item.strip()

        # 只有日期，例如 11
        if "/" not in item:

            item = f"{last_month}/{item}"

        if item.count("/") == 1:

            month = item.split("/")[0]
            last_month = month
            item = f"{year}/{item}"

        result.append(
            datetime.strptime(
                item,
                "%Y/%m/%d"
            ).strftime("%Y/%m/%d")
        )

    return result


def get_first_show_date(show):

    dates = split_show_dates(show["演出日期"])

    return dates[0]


def get_last_show_date(show):

    dates = split_show_dates(show["演出日期"])

    return dates[-1]


def normalize_show_date(value):

    return "、".join(
        split_show_dates(value)
    )


def normalize_ticket_time(value):

    value = value.strip().replace("-", "/")
    date_part, time_part = value.split(" ", 1)

    if date_part.count("/") == 1:
        date_part = f"{datetime.now().year}/{date_part}"

    result = datetime.strptime(
        f"{date_part} {time_part}",
        "%Y/%m/%d %H:%M"
    )

    return result.strftime("%Y/%m/%d %H:%M")


def normalize_pickup_date(value, show_date):

    value = value.strip().replace("-", "/")

    if value == "略過":
        return ""

    if value.endswith("天前"):

        days = int(
            value.replace("天前", "").strip()
        )

        event_date = datetime.strptime(
            show_date,
            "%Y/%m/%d"
        )

        return (
            event_date - timedelta(days=days)
        ).strftime("%Y/%m/%d")

    return normalize_show_date(value)


def start_add_show(event, user_id):

    user_state[user_id] = {
        "mode": "新增演出",
        "step": "name",
        "data": {}
    }

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=(
                "➕ 新增演出\n\n"
                "請輸入演出名稱\n\n"
                "例如：五月天演唱會"
            ),
            quick_reply=simple_quick_reply([
                ("❌ 取消", "取消")
            ])
        )
    )

    return True


def handle_add_show_flow(event, text, user_id):

    state = user_state.get(user_id)

    if not isinstance(state, dict):
        return False

    if state.get("mode") != "新增演出":
        return False

    if text == "取消":

        user_state.pop(user_id, None)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="已取消新增演出"
            )
        )

        return True

    data = state.setdefault("data", {})
    step = state.get("step")

    if step == "name":

        data["演出名稱"] = text
        state["step"] = "show_date"

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=(
                    "📅 請輸入演出日期\n\n"
                    "例如：10/1\n"
                    "或：2026/10/1"
                ),
                quick_reply=simple_quick_reply([
                    ("❌ 取消", "取消")
                ])
            )
        )

        return True

    if step == "show_date":

        try:
            data["演出日期"] = normalize_show_date(text)

        except Exception:

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=(
                        "❌ 日期格式不正確\n\n"
                        "請輸入：10/1\n"
                        "或：2026/10/1"
                    ),
                    quick_reply=simple_quick_reply([
                        ("❌ 取消", "取消")
                    ])
                )
            )

            return True

        state["step"] = "ticket_time"

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=(
                    "🎟 請輸入搶票時間\n\n"
                    "例如：9/1 12:00\n"
                    "或：2026/9/1 12:00"
                ),
                quick_reply=simple_quick_reply([
                    ("❌ 取消", "取消")
                ])
            )
        )

        return True

    if step == "ticket_time":

        try:
            data["搶票時間"] = normalize_ticket_time(text)

        except Exception:

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=(
                        "❌ 搶票時間格式不正確\n\n"
                        "請輸入：9/1 12:00"
                    ),
                    quick_reply=simple_quick_reply([
                        ("❌ 取消", "取消")
                    ])
                )
            )

            return True

        state["step"] = "price"

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=(
                    "💰 請輸入價格與張數\n\n"
                    "例如：$3800*2"
                ),
                quick_reply=simple_quick_reply([
                    ("❌ 取消", "取消")
                ])
            )
        )

        return True

    if step == "price":

        data["價格張數"] = text
        state["step"] = "platform"

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="🌐 請選擇或直接輸入售票平台",
                quick_reply=simple_quick_reply([
                    ("拓元", "拓元"),
                    ("KKTIX", "KKTIX"),
                    ("ibon", "ibon"),
                    ("寬宏", "寬宏"),
                    ("年代", "年代"),
                    ("❌ 取消", "取消")
                ])
            )
        )

        return True

    if step == "platform":

        data["售票平台"] = text
        state["step"] = "pickup_date"

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=(
                    "🎫 請輸入取票日期\n\n"
                    "例如：5天前\n"
                    "或：9/25\n\n"
                    "沒有取票提醒可按略過"
                ),
                quick_reply=simple_quick_reply([
                    ("3天前", "3天前"),
                    ("5天前", "5天前"),
                    ("7天前", "7天前"),
                    ("➖ 略過", "略過"),
                    ("❌ 取消", "取消")
                ])
            )
        )

        return True

    if step == "pickup_date":

        try:
            data["取票日期"] = normalize_pickup_date(
                text,
                data["演出日期"]
            )

        except Exception:

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=(
                        "❌ 取票日期格式不正確\n\n"
                        "請輸入：5天前\n"
                        "或：2026/9/25"
                    ),
                    quick_reply=simple_quick_reply([
                        ("➖ 略過", "略過"),
                        ("❌ 取消", "取消")
                    ])
                )
            )

            return True

        state["step"] = "note"

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=(
                    "📝 請輸入備註\n\n"
                    "例如：會員預售\n\n"
                    "沒有備註可按略過"
                ),
                quick_reply=simple_quick_reply([
                    ("➖ 略過", "略過"),
                    ("❌ 取消", "取消")
                ])
            )
        )

        return True

    if step == "note":

        data["備註"] = "" if text == "略過" else text
        state["step"] = "confirm"

        reply = (
            "📋 請確認新增資料\n\n"
            f"🎤 {data['演出名稱']}\n"
            f"📅 演出日期：{data['演出日期']}\n"
            f"🎟 搶票時間：{data['搶票時間']}\n"
            f"💰 價格張數：{data['價格張數']}\n"
            f"🌐 售票平台：{data['售票平台']}\n"
            f"🎫 取票日期：{data.get('取票日期') or '未設定'}\n"
            f"📝 備註：{data.get('備註') or '無'}"
        )

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=reply,
                quick_reply=simple_quick_reply([
                    ("✅ 確認新增", "確認新增"),
                    ("🔄 重新填寫", "重新填寫"),
                    ("❌ 取消", "取消")
                ])
            )
        )

        return True

    if step == "confirm":

        if text == "重新填寫":

            state["step"] = "name"
            state["data"] = {}

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="請重新輸入演出名稱",
                    quick_reply=simple_quick_reply([
                        ("❌ 取消", "取消")
                    ])
                )
            )

            return True

        if text != "確認新增":

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="請使用下方按鈕確認",
                    quick_reply=simple_quick_reply([
                        ("✅ 確認新增", "確認新增"),
                        ("🔄 重新填寫", "重新填寫"),
                        ("❌ 取消", "取消")
                    ])
                )
            )

            return True

        show = {
            "演出名稱": data.get("演出名稱", ""),
            "演出日期": data.get("演出日期", ""),
            "搶票時間": data.get("搶票時間", ""),
            "價格張數": data.get("價格張數", ""),
            "售票平台": data.get("售票平台", ""),
            "取票日期": data.get("取票日期", ""),
            "備註": data.get("備註", ""),
            "搶票狀態": "等待搶票",
            "取票狀態": "未取票",
            "搶票大師": "",
            "取票人": "",
            "提醒": {
                "前一天": False,
                "30分鐘": False,
                "10分鐘": False,
                "取票": False,
                "演出日": False
            }
        }

        try:

            supabase.table("shows").insert(
                show
            ).execute()

        except Exception as e:

            print("新增演出失敗：", repr(e), flush=True)

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"❌ 新增失敗\n{e}"
                )
            )

            return True

        user_state.pop(user_id, None)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=(
                    "✅ 新增成功\n\n"
                    f"🎤 {show['演出名稱']}\n"
                    f"📅\n{format_show_dates(show['演出日期'])}\n"
                    f"🎟 {show['搶票時間']}"
                )
            )
        )

        return True

    user_state.pop(user_id, None)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text="❌ 新增狀態異常，請重新操作"
        )
    )

    return True


def edit_field_quick_reply():

    return simple_quick_reply([
        ("🎤 演出名稱", "演出名稱"),
        ("📅 演出日期", "演出日期"),
        ("🎟 搶票時間", "搶票時間"),
        ("💰 價格張數", "價格張數"),
        ("🌐 售票平台", "售票平台"),
        ("🎫 取票日期", "取票日期"),
        ("📝 備註", "備註"),
        ("❌ 取消", "取消")
    ])


def start_edit_show(event, text, user_id):

    previous_state = user_state.get(user_id)

    if previous_state == "搶票列表":
        shows = get_waiting_shows()
    elif previous_state == "取票列表":
        shows = get_pickup_shows()
    else:
        shows = get_all_shows()

    try:

        index = int(
            text.replace("修改", "").strip()
        ) - 1

    except Exception:

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="請輸入格式：\n修改 1"
            )
        )

        return True

    if index < 0 or index >= len(shows):

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="❌ 找不到這筆演出"
            )
        )

        return True

    show = shows[index]

    user_state[user_id] = {
        "mode": "修改演出",
        "step": "field",
        "show_id": show["id"],
        "data": {
            "show_name": show.get("演出名稱", "")
        }
    }

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=(
                f"✏️ 修改演出\n\n"
                f"🎤 {show.get('演出名稱', '')}\n\n"
                "請選擇要修改的欄位"
            ),
            quick_reply=edit_field_quick_reply()
        )
    )

    return True


def handle_edit_show_flow(event, text, user_id):

    state = user_state.get(user_id)

    if not isinstance(state, dict):
        return False

    if state.get("mode") != "修改演出":
        return False

    if text == "取消":

        user_state.pop(user_id, None)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="已取消修改演出"
            )
        )

        return True

    if state.get("step") == "field":

        allowed_fields = {
            "演出名稱",
            "演出日期",
            "搶票時間",
            "價格張數",
            "售票平台",
            "取票日期",
            "備註"
        }

        if text not in allowed_fields:

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="請使用下方按鈕選擇欄位",
                    quick_reply=edit_field_quick_reply()
                )
            )

            return True

        state["field"] = text
        state["step"] = "value"

        hints = {
            "演出名稱": "請輸入新的演出名稱",
            "演出日期": "請輸入新的演出日期\n例如：10/1",
            "搶票時間": "請輸入新的搶票時間\n例如：9/1 12:00",
            "價格張數": "請輸入新的價格張數\n例如：$3800*2",
            "售票平台": "請輸入新的售票平台",
            "取票日期": "請輸入新的取票日期\n例如：5天前、9/25\n也可按「清除」",
            "備註": "請輸入新的備註\n也可按「清除」"
        }

        buttons = [("❌ 取消", "取消")]

        if text in {"取票日期", "備註"}:
            buttons.insert(0, ("🗑 清除", "清除"))

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=hints[text],
                quick_reply=simple_quick_reply(buttons)
            )
        )

        return True

    if state.get("step") == "value":

        field = state.get("field")

        shows = load_data()

        show = next(
            (
                item
                for item in shows
                if item.get("id") == state.get("show_id")
            ),
            None
        )

        if not show:

            user_state.pop(user_id, None)

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="❌ 找不到這筆演出，請重新操作"
                )
            )

            return True

        try:

            if field == "演出日期":
                new_value = normalize_show_date(text)

            elif field == "搶票時間":
                new_value = normalize_ticket_time(text)

            elif field == "取票日期":

                if text == "清除":
                    new_value = ""
                else:
                    new_value = normalize_pickup_date(
                        text,
                        show.get("演出日期", "")
                    )

            elif field == "備註" and text == "清除":
                new_value = ""

            else:
                new_value = text

        except Exception:

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=(
                        "❌ 格式不正確，請重新輸入\n\n"
                        "輸入「取消」可取消修改"
                    )
                )
            )

            return True

        old_value = show.get(field, "")
        show[field] = new_value

        try:
            update_show(show)

        except Exception as e:

            print("修改演出失敗：", repr(e), flush=True)

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"❌ 修改失敗\n{e}"
                )
            )

            return True

        user_state.pop(user_id, None)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=(
                    "✅ 修改成功\n\n"
                    f"🎤 {show.get('演出名稱', '')}\n"
                    f"✏️ 欄位：{field}\n"
                    f"原本：{old_value or '無'}\n"
                    f"修改後：{format_show_dates(new_value) if field == '演出日期' else (new_value or '無')}"
                )
            )
        )

        return True

    user_state.pop(user_id, None)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text="❌ 修改狀態異常，請重新操作"
        )
    )

    return True


# =====================
# 完成搶票
# =====================

def handle_complete_ticket(event, text, user_id):

    shows = get_all_shows()

    try:

        index = int(
            text.replace("完成搶票", "").strip()
        ) - 1

        if index < 0 or index >= len(shows):

            return TextSendMessage(
                text="❌ 找不到這筆演出"
            )

        show = shows[index]

        if show.get("搶票狀態") == "已搶票":

            return TextSendMessage(
                text="⚠️ 這筆演出已經完成搶票"
            )

        user_state[user_id] = {
            "mode": "完成搶票",
            "step": "master",
            "show_id": show["id"],
            "data": {
                "搶票大師": "",
                "取票人": []
            }
        }

        return TextSendMessage(
            text=(
                f"🎤 {show['演出名稱']}\n\n"
                "請選擇搶票大師"
            ),
            quick_reply=member_quick_reply(
                allow_finish=False,
                allow_skip=True
            )
        )

    except Exception as e:

        print("完成搶票指令錯誤：", e)

        return TextSendMessage(
            text=(
                "請輸入：\n"
                "完成搶票 1"
            )
        )

# =====================
# 完成搶票問答流程
# =====================

def send_member_picker(
    event,
    title,
    selected=None,
    allow_finish=False,
    allow_skip=True
):

    selected = selected or []

    if selected:

        selected_text = "\n".join(
            f"👤 {name}"
            for name in selected
        )

        message = (
            f"{title}\n\n"
            f"目前已選：\n"
            f"{selected_text}"
        )

    else:

        message = (
            f"{title}\n\n"
            "目前已選：無"
        )

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=message,
            quick_reply=member_quick_reply(
                selected=selected,
                allow_finish=allow_finish,
                allow_skip=allow_skip
            )
        )
    )

def handle_complete_ticket_flow(event, text, user_id):

    state = user_state.get(user_id)

    if not isinstance(state, dict):
        return False

    if state.get("mode") != "完成搶票":
        return False

    # 任何階段都可以取消
    if text == "取消":

        user_state.pop(user_id, None)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="已取消完成搶票"
            )
        )

        return True

    data = state.setdefault(
        "data",
        {
            "搶票大師": "",
            "取票人": []
        }
    )

    data.setdefault("搶票大師", "")
    data.setdefault("取票人", [])

    # =====================
    # 第一步：選擇搶票大師
    # =====================

    if state.get("step") == "master":

        if text == "略過":
            master = ""

        else:
            members = load_members()

            if text not in members:

                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="請使用下方按鈕選擇搶票大師",
                        quick_reply=member_quick_reply(
                            allow_finish=False,
                            allow_skip=True
                        )
                    )
                )

                return True

            master = text

        data["搶票大師"] = master
        state["step"] = "people"

        send_member_picker(
            event=event,
            title="請選擇取票人",
            selected=data["取票人"],
            allow_finish=True,
            allow_skip=True
        )

        return True

    # =====================
    # 第二步：多選取票人
    # =====================

    if state.get("step") == "people":

        selected_people = data.setdefault(
            "取票人",
            []
        )

        # 略過取票人，直接完成
        if text == "略過":

            selected_people.clear()

            return finish_complete_ticket(
                event,
                user_id,
                state
            )

        # 按完成後寫入 Supabase
        if text == "完成":

            return finish_complete_ticket(
                event,
                user_id,
                state
            )

        members = load_members()

        if text not in members:

            send_member_picker(
                event=event,
                title="請使用下方按鈕選擇取票人",
                selected=selected_people,
                allow_finish=True,
                allow_skip=True
            )

            return True

        # 避免重複加入
        if text not in selected_people:
            selected_people.append(text)

        send_member_picker(
            event=event,
            title="請繼續選擇取票人，選好後按「完成」",
            selected=selected_people,
            allow_finish=True,
            allow_skip=False
        )

        return True

    # 狀態異常時清除
    user_state.pop(user_id, None)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text="❌ 操作狀態異常，請重新執行完成搶票"
        )
    )

    return True

def finish_complete_ticket(
    event,
    user_id,
    state
):

    shows = load_data()

    show = next(
        (
            item
            for item in shows
            if item.get("id") == state.get("show_id")
        ),
        None
    )

    if not show:

        user_state.pop(user_id, None)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="❌ 找不到這筆演出，請重新操作"
            )
        )

        return True

    data = state.get("data", {})

    selected_people = data.get(
        "取票人",
        []
    )

    if not isinstance(selected_people, list):
        selected_people = []

    show["搶票大師"] = data.get(
        "搶票大師",
        ""
    )

    show["取票人"] = "、".join(
        selected_people
    )

    show["搶票狀態"] = "已搶票"

    try:

        update_show(show)

    except Exception as e:

        print(
            "完成搶票更新錯誤：",
            e,
            flush=True
        )

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=f"❌ 更新失敗\n{e}"
            )
        )

        return True

    user_state.pop(user_id, None)

    reply = (
        "✅ 已完成搶票\n\n"
        f"🎤 {show['演出名稱']}\n"
        f"🎟 搶票大師："
        f"{show.get('搶票大師') or '未設定'}\n"
        f"👥 取票人："
        f"{show.get('取票人') or '無'}\n"
        "📌 狀態：已搶票"
    )

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=reply
        )
    )

    return True

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
                    f"{show['價格張數']}\n\n"

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


        except Exception as e:

            print(e)

            reply = "請輸入格式：\n查看 1"



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
