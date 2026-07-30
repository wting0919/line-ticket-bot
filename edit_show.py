from linebot.models import TextSendMessage

from data import (
    load_data,
    update_show,
)

from utils import (
    normalize_show_date,
    normalize_ticket_time,
    normalize_pickup_date,
    format_show_dates,
)

from ui import (
    simple_quick_reply,
    edit_field_quick_reply,
)

from show_list import (
    get_waiting_shows,
    get_pickup_shows,
    get_all_shows,
)

line_bot_api = None
user_state = {}

ALLOWED_FIELDS = {
    "演出名稱",
    "演出日期",
    "搶票時間",
    "價格張數",
    "售票平台",
    "取票日期",
    "備註",
}

FIELD_HINTS = {
    "演出名稱": "請輸入新的演出名稱",
    "演出日期": "請輸入新的演出日期\n例如：10/1",
    "搶票時間": "請輸入新的搶票時間\n例如：9/1 12:00",
    "價格張數": "請輸入新的價格張數\n例如：$3800*2",
    "售票平台": "請輸入新的售票平台",
    "取票日期": "請輸入新的取票日期\n例如：5天前、9/25\n也可按「清除」",
    "備註": "請輸入新的備註\n也可按「清除」",
}


def start_edit_show(event, text, user_id):

    state = user_state.get(user_id)

    if state == "搶票列表":
        shows = get_waiting_shows()

    elif state == "取票列表":
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
    }

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=(
                "✏️ 修改演出\n\n"
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

        if text not in ALLOWED_FIELDS:

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

        buttons = [("❌ 取消", "取消")]

        if text in {"取票日期", "備註"}:
            buttons.insert(0, ("🗑 清除", "清除"))

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=FIELD_HINTS[text],
                quick_reply=simple_quick_reply(buttons)
            )
        )

        return True

    if state.get("step") == "value":

        field = state["field"]

        shows = load_data()

        show = next(
            (item for item in shows if item["id"] == state["show_id"]),
            None
        )

        if show is None:

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

            elif field == "備註":

                if text == "清除":
                    new_value = ""
                else:
                    new_value = text

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

        if field == "演出日期":
            display_value = format_show_dates(new_value)
        else:
            display_value = new_value or "無"

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=(
                    "✅ 修改成功\n\n"
                    f"🎤 {show.get('演出名稱', '')}\n"
                    f"✏️ 欄位：{field}\n"
                    f"原本：{old_value or '無'}\n"
                    f"修改後：{display_value}"
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