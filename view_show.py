from linebot.models import TextSendMessage

from utils import (
    format_price,
    format_datetime,
    format_show_dates,
)

from show_list import (
    get_all_shows,
)

line_bot_api = None
user_state = {}


# =====================
# 查看功能
# =====================

def handle_view_show(
    event,
    text,
    user_id,
):

    state = user_state.get(user_id)

    if isinstance(state, dict) and "shows" in state:

        shows = state["shows"]

    else:

        shows = get_all_shows()

    try:

        index = int(
            text.replace("查看", "").strip()
        ) - 1

        if index < 0 or index >= len(shows):

            reply = "❌ 找不到這筆演出"

        else:

            show = shows[index]

            note = show.get("備註") or "無"

            status = show.get("搶票狀態", "等待搶票")

            if status == "已搶票":
                ticket_status = "✅ 已搶票"

            elif status == "未搶到":
                ticket_status = "❌ 未搶到"

            else:
                ticket_status = "⏳ 等待搶票"

            if show.get("取票狀態") == "已取票":
                pickup_status = "✅ 已取票"
            else:
                pickup_status = "🎫 未取票"

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
            )

            reply += (
                "\n\n"
                "📌 搶票\n"
                f"{ticket_status}"
            )

            if status == "已搶票":

                reply += (
                    "\n\n"
                    "📌 取票\n"
                    f"{pickup_status}\n\n"
                    "👤 搶票大師\n"
                    f"{show.get('搶票大師') or '未設定'}\n\n"
                    "👥 取票人\n"
                    f"{show.get('取票人') or '未設定'}"
                )

            reply += (
                "\n\n"
                "📝 備註\n"
                f"{note}"
            )

            # ===== 可執行操作 =====

            reply += "\n\n────────────\n"

            if status == "等待搶票":

                reply += (
                    "可執行：\n"
                    f"✅ 完成搶票 {index + 1}\n"
                    f"❌ 未搶到 {index + 1}\n"
                    f"✏️ 修改 {index + 1}\n"
                    f"🗑️ 刪除 {index + 1}"
                )

            elif status == "已搶票":

                if show.get("取票狀態") == "已取票":

                    reply += (
                        "可執行：\n"
                        f"✏️ 修改 {index + 1}\n"
                        f"🗑️ 刪除 {index + 1}"
                    )

                else:

                    reply += (
                        "可執行：\n"
                        f"🎫 完成取票 {index + 1}\n"
                        f"✏️ 修改 {index + 1}\n"
                        f"🗑️ 刪除 {index + 1}"
                    )

            elif status == "未搶到":

                reply += (
                    "可執行：\n"
                    f"✏️ 修改 {index + 1}\n"
                    f"🗑️ 刪除 {index + 1}"
                )

    except ValueError:

        reply = "請輸入格式：\n查看 1"

    except Exception as e:

        print("查看錯誤：", e)

        reply = f"❌ 發生錯誤\n{e}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=reply
        )
    )

    return True