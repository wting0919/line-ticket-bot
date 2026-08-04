import config

from linebot.models import TextSendMessage

from data import (
    insert_show,
)

from utils import (
    normalize_show_date,
    normalize_ticket_time,
    normalize_pickup_date,
    format_show_dates,
    format_datetime,
)

from ui import (
    simple_quick_reply,
)

from helpers import (
    get_state,
    set_state,
    clear_state,
)


def start_add_show(event, user_id):

    set_state(
        user_id,
        {
            "mode": "新增演出",
            "step": "artist",
            "data": {}
        }
    )

    config.line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=(
                "➕ 新增演出\n\n"
                "請輸入藝人\n\n"
                "例如：SEVENTEEN"
            ),
            quick_reply=simple_quick_reply([
                ("❌ 取消", "取消")
            ])
        )
    )

    return True


def handle_add_show_flow(event, text, user_id):

    state = get_state(user_id)

    if not isinstance(state, dict):
        return False

    if state.get("mode") != "新增演出":
        return False

    if text == "取消":

        clear_state(user_id)

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="已取消新增演出"
            )
        )

        return True

    data = state.setdefault("data", {})
    step = state.get("step")

    if step == "artist":

        data["藝人"] = text
        state["step"] = "activity"

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=(
                    "🎤 請選擇活動類型"
                ),
                quick_reply=simple_quick_reply([
                    ("演唱會", "演唱會"),
                    ("FM", "FM"),
                    ("FP", "FP"),
                    ("LIVE", "LIVE"),
                    ("SHOWCASE", "SHOWCASE"),
                    ("拼盤", "拼盤"),
                    ("其他", "其他"),
                    ("❌ 取消", "取消"),
                ])
            )
        )

        return True


    if step == "activity":

        data["活動"] = text
        state["step"] = "activity_name"

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=(
                    "🏷️ 請輸入活動名稱\n\n"
                    "例如：BE THE SUN\n\n"
                    "沒有可按略過"
                ),
                quick_reply=simple_quick_reply([
                    ("➖ 略過", "略過"),
                    ("❌ 取消", "取消"),
                ])
            )
        )

        return True


    if step == "activity_name":

        data["活動名稱"] = "" if text == "略過" else text
        state["step"] = "show_date"

        config.line_bot_api.reply_message(
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

        except ValueError:

            config.line_bot_api.reply_message(
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

        config.line_bot_api.reply_message(
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

        except ValueError:

            config.line_bot_api.reply_message(
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

        config.line_bot_api.reply_message(
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

        config.line_bot_api.reply_message(
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

        config.line_bot_api.reply_message(
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

        except ValueError:

            config.line_bot_api.reply_message(
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

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=(
                    "📝 請輸入備註\n\n"
                    "例如：會員預售or卡友優先or公售\n\n"
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
            "📋 請確認新增資料\n"
            "──────────\n"
            f"🎤 {data['藝人']}\n"
            f"🏷️ {data['活動']}\n"
        )

        if data.get("活動名稱"):
            reply += f"✨ {data['活動名稱']}\n"

        reply += (
            f"📅 {format_show_dates(data['演出日期'])}\n"
            f"🎟 {data['搶票時間']}\n"
            f"💰 {data['價格張數']}\n"
            f"🌐 {data['售票平台']}\n"
            f"📦 {data.get('取票日期') or '未設定'}\n"
            f"📝 {data.get('備註') or '無'}"
        )

        config.line_bot_api.reply_message(
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

            state["step"] = "artist"
            state["data"] = {}

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="請重新輸入藝人",
                    quick_reply=simple_quick_reply([
                        ("❌ 取消", "取消")
                    ])
                )
            )

            return True

        if text != "確認新增":

            config.line_bot_api.reply_message(
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
            "藝人": data.get("藝人", ""),
            "活動": data.get("活動", ""),
            "活動名稱": data.get("活動名稱", ""),

            # 先保留舊欄位
            "演出名稱": (
                data.get("藝人", "")
                + (
                    f" {data.get('活動名稱', '')}"
                    if data.get("活動名稱")
                    else ""
                )
            ).strip(),

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
                "演出日": False,
            },
        }

        try:

            show = insert_show(show)

        except Exception as e:

            print("新增演出失敗：", repr(e), flush=True)

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"❌ 新增失敗\n{e}"
                )
            )

            return True

        clear_state(user_id)

        config.line_bot_api.reply_message(
            event.reply_token,
            success = (
                "✅ 已新增演出\n"
                "──────────\n"
                f"🎤 {show['藝人']}\n"
                f"🏷️ {show['活動']}\n"
            )

            if show.get("活動名稱"):
                success += f"✨ {show['活動名稱']}\n"

            success += (
                f"📅 {format_show_dates(show['演出日期'])}\n"
                f"🎟 {format_datetime(show['搶票時間'])}"
            )

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=success
                )
            )
        )

        return True

    clear_state(user_id)

    config.line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text="❌ 新增狀態異常，請重新操作"
        )
    )

    return True
