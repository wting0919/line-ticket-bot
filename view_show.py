from linebot.models import (
    TextSendMessage,
    QuickReply,
    QuickReplyButton,
    MessageAction,
)

from utils import (
    format_price,
    format_datetime,
    format_show_dates,
)

from show_list import (
    get_all_shows,
)

from helpers import (
    get_current_shows,
    get_state,
    set_current_index,
)

import config


# =====================
# Quick Reply
# =====================

def view_quick_reply(index, status, pickup_status):

    items = [
        QuickReplyButton(
            action=MessageAction(label="⬅️ 上一筆", text="上一筆")
        ),
        QuickReplyButton(
            action=MessageAction(label="➡️ 下一筆", text="下一筆")
        ),
    ]

    if status == "等待搶票":

        items.append(
            QuickReplyButton(
                action=MessageAction(
                    label="✅ 完成搶票",
                    text=f"完成搶票 {index}"
                )
            )
        )

        items.append(
            QuickReplyButton(
                action=MessageAction(
                    label="❌ 未搶到",
                    text=f"未搶到 {index}"
                )
            )
        )

    elif status == "已搶票" and pickup_status != "已取票":

        items.append(
            QuickReplyButton(
                action=MessageAction(
                    label="🎫 完成取票",
                    text=f"完成取票 {index}"
                )
            )
        )

    items.extend([
        QuickReplyButton(
            action=MessageAction(label="✏️ 修改", text=f"修改 {index}")
        ),
        QuickReplyButton(
            action=MessageAction(label="📄 複製", text=f"複製 {index}")
        ),
        QuickReplyButton(
            action=MessageAction(label="🗑️ 刪除", text=f"刪除 {index}")
        ),
    ])

    return QuickReply(items=items)


# =====================
# 查看功能
# =====================

def handle_view_show(event, text, user_id):

    state = get_state(user_id)

    shows = get_current_shows(user_id)

    if shows is None:
        shows = get_all_shows()

    try:

        index = int(text.replace("查看", "").strip()) - 1

        if index < 0 or index >= len(shows):
            reply = "❌ 找不到這筆演出"

        else:

            show = shows[index]

            if isinstance(state, dict):
                set_current_index(user_id, index)

            note = show.get("備註") or "無"
            status = show.get("搶票狀態", "等待搶票")

            ticket_status = {
                "已搶票": "✅ 已搶票",
                "未搶到": "❌ 未搶到",
            }.get(status, "⏳ 等待搶票")

            pickup_status = (
                "✅ 已取票"
                if show.get("取票狀態") == "已取票"
                else "🎫 未取票"
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
                f"{show['售票平台']}"
            )

            reply += "\n\n📌 搶票\n" + ticket_status

            if status == "已搶票":
                reply += (
                    "\n\n📌 取票\n"
                    f"{pickup_status}\n\n"
                    "👤 搶票大師\n"
                    f"{show.get('搶票大師') or '未設定'}\n\n"
                    "👥 取票人\n"
                    f"{show.get('取票人') or '未設定'}"
                )

            reply += "\n\n📝 備註\n" + note

    except ValueError:
        reply = "請輸入格式：\n查看 1"

    except Exception as e:
        print("查看錯誤：", e)
        reply = f"❌ 發生錯誤\n{e}"

    if not reply.startswith("🎫 演出資訊"):
        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply)
        )
        return True

    config.line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=reply,
            quick_reply=view_quick_reply(
                index + 1,
                status,
                show.get("取票狀態")
            )
        )
    )

    return True