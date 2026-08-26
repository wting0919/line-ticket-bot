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
    get_all_shows,
)

from helpers import (
    get_state,
    set_state,
    clear_state,
)

from theme import (
    activity_quick_reply,
    reminder_quick_reply,
    reminder_message,
    ACTIVITY_VALUES,
    REMINDER_OPTIONS,
)

import config


ALLOWED_FIELDS = {
    "藝人",
    "活動",
    "活動名稱",
    "演出日期",
    "搶票時間",
    "價格張數",
    "售票平台",
    "售票網址",
    "會員資訊",
    "注意事項",
    "售票階段",
    "取票日期",
    "備註",
}

FIELD_HINTS = {
    "藝人": "請輸入新的藝人",
    "活動": "請選擇新的活動類型",
    "活動名稱": "請輸入新的活動名稱",
    "演出日期": "請輸入新的演出日期\n例如：10/1",
    "搶票時間": "請輸入新的搶票時間\n例如：9/1 12:00",
    "價格張數": "請輸入新的價格張數\n例如：3800*2",
    "售票平台": "請輸入新的售票平台",
    "售票網址": "請輸入新的售票網址\n例如：https://tixcraft.com/",
    "會員資訊": "請輸入新的會員資訊\n也可按「清除」",
    "注意事項": "請選擇新的注意事項",
    "售票階段": "請選擇新的售票階段",
    "取票日期": "請輸入新的取票日期\n例如：5天前、9/25\n也可按「清除」",
    "備註": "請輸入新的備註\n也可按「清除」",
}


def start_edit_show(event, text, user_id):

    state = get_state(user_id)

    if isinstance(state, dict) and "shows" in state:

        shows = state["shows"]

    else:

        shows = get_all_shows()

    try:
        show_id = int(
            text.replace("修改ID", "").strip()
        )

    except ValueError:

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="請輸入格式：\n修改ID 5"
            )
        )

        return True

    show = next(
        (
            item
            for item in shows
            if item.get("id") == show_id
        ),
        None
    )

    if show is None:

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="❌ 找不到這筆演出"
            )
        )

        return True


    set_state(
        user_id,
        {
            "mode": "修改演出",
            "step": "field",
            "show_id": show["id"],
            "field_page": 1,
        }
    )

    config.line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=(
                "✏️ 修改演出\n\n"
                f"🎤 {show.get('藝人', '')}\n"
                + (
                    f"✨ {show.get('活動名稱')}\n\n"
                    if show.get("活動名稱")
                    else "\n"
                )
                + "請選擇要修改的欄位"
            ),
            quick_reply=edit_field_quick_reply(1)
        )
    )

    return True


def handle_edit_show_flow(event, text, user_id):

    state = get_state(user_id)

    if (
        not isinstance(state, dict)
        or state.get("mode") != "修改演出"
    ):
        return False

    if text == "取消":

        clear_state(user_id)

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="已取消修改演出"
            )
        )

        return True

    if state.get("step") == "field":

        if text == "修改下一頁":

            state["field_page"] = 2

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="✏️ 請選擇要修改的欄位",
                    quick_reply=edit_field_quick_reply(2)
                )
            )

            return True


         if text == "修改上一頁":

             state["field_page"] = 1

             config.line_bot_api.reply_message(
                 event.reply_token,
                 TextSendMessage(
                     text="✏️ 請選擇要修改的欄位",
                     quick_reply=edit_field_quick_reply(1)
                 )
            )

            return True


    if text not in ALLOWED_FIELDS:

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="請使用下方按鈕選擇欄位",
                quick_reply=edit_field_quick_reply(
                    state.get("field_page", 1)
                )
            )
        )

        return True

        if text not in ALLOWED_FIELDS:

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="請使用下方按鈕選擇欄位",
                    quick_reply=edit_field_quick_reply()
                )
            )

            return True

        if text == "活動":

            state["field"] = "活動"
            state["step"] = "activity"

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="🏷 請選擇活動類型",
                    quick_reply=activity_quick_reply()
                )
            )

            return True

        if text == "售票階段":

            state["field"] = "售票階段"
            state["step"] = "sale_stage"

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="🚩 請選擇新的售票階段",
                    quick_reply=simple_quick_reply([
                        ("會員預售", "會員預售"),
                        ("卡友優先", "卡友優先"),
                        ("公售", "公售"),
                        ("❌ 取消", "取消"),
                    ])
                )
            )

            return True

        if text == "注意事項":

            state["field"] = "注意事項"
            state["step"] = "reminder"

            show = next(
                (
                    item
                    for item in load_data()
                    if item["id"] == state["show_id"]
                ),
                None,
            )

            state["selected_reminders"] = (
                show.get("注意事項", "").splitlines()
                if show and show.get("注意事項")
                else []
            )

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=reminder_message(
                        state["selected_reminders"]
                    ),
                    quick_reply=reminder_quick_reply(),
                )
            )

            return True

        state["field"] = text
        state["step"] = "value"

        buttons = []

        if text in {
            "會員資訊",
            "售票網址",
            "取票日期",
            "備註",
        }:
            buttons.append(("🗑 清除", "清除"))

        buttons.append(("❌ 取消", "取消"))

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=FIELD_HINTS[text],
                quick_reply=simple_quick_reply(buttons)
            )
        )

        return True

    if state.get("step") == "activity":

        if text == "取消":

            clear_state(user_id)

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="已取消修改演出")
            )

            return True

        if text not in ACTIVITY_VALUES:

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="請使用下方按鈕選擇活動類型",
                    quick_reply=activity_quick_reply()
                )
            )

            return True

        show = next(
            (
                item
                for item in load_data()
                if item["id"] == state["show_id"]
            ),
            None,
        )

        if show is None:
            clear_state(user_id)
            return True

        old_value = show.get("活動") or "其他"

        show["活動"] = text

        update_show(show)

        clear_state(user_id)

        header = (
            "✅ 修改成功\n"
            "──────────\n"
            f"🎤 {show.get('藝人', '')}\n"
            f"🏷️ {show.get('活動', '')}\n"
        )

        if show.get("活動名稱"):
            header += f"✨ {show['活動名稱']}\n"

        header += "──────────\n"

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=(
                    header
                    + "✏️ 活動\n"
                    + f"🔸 原本：{old_value}\n"
                    + f"🔹 修改後：{text}"
                )
            )
        )

        return True

    if state.get("step") == "reminder":

        selected = state.setdefault(
            "selected_reminders",
            []
        )

        if text == "略過":

            show = next(
                (
                    item
                    for item in load_data()
                    if item["id"] == state["show_id"]
                ),
                None,
            )

            if show is None:
                clear_state(user_id)
                return True

            old_value = show.get("注意事項") or ""

            show["注意事項"] = ""

            update_show(show)

            clear_state(user_id)

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=(
                        "✅ 修改成功\n"
                        "──────────\n"
                        f"🎤 {show.get('藝人', '')}\n"
                        f"🏷️ {show.get('活動', '')}\n"
                        + (
                            f"✨ {show.get('活動名稱')}\n"
                            if show.get("活動名稱")
                            else ""
                        )
                        + "──────────\n"
                        "✏️ 注意事項\n"
                        f"🔸 原本：{old_value or '無'}\n"
                        "🔹 修改後：無"
                    )
                )
            )

            return True

        if text == "完成":

            if not selected:

                config.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="請至少選擇一項，或按「略過」",
                        quick_reply=reminder_quick_reply(),
                    )
                )

                return True

            show = next(
                (
                    item
                    for item in load_data()
                    if item["id"] == state["show_id"]
                ),
                None,
            )

            if show is None:
                clear_state(user_id)
                return True

            old_value = show.get("注意事項") or ""

            new_value = "\n".join(selected)

            show["注意事項"] = new_value

            update_show(show)

            clear_state(user_id)

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=(
                        "✅ 修改成功\n"
                        "──────────\n"
                        f"🎤 {show.get('藝人', '')}\n"
                        f"🏷️ {show.get('活動', '')}\n"
                        + (
                            f"✨ {show.get('活動名稱')}\n"
                            if show.get("活動名稱")
                            else ""
                        )
                        + "──────────\n"
                        "✏️ 注意事項\n"
                        f"🔸 原本：{old_value or '無'}\n"
                        f"🔹 修改後：{new_value}"
                    )
                )
            )

            return True

        if text == "自訂提醒":

            state["step"] = "custom_reminder"

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="請輸入注意事項"
                )
            )

            return True

        if text in REMINDER_OPTIONS:

            if text not in selected:

                selected.append(text)

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=reminder_message(selected),
                    quick_reply=reminder_quick_reply(),
                )
            )

            return True

    if state.get("step") == "custom_reminder":

        text = text.strip()

        if not text:

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="注意事項不可空白"
                )
            )

            return True

        selected = state.setdefault(
            "selected_reminders",
            []
        )

        if text not in selected:

            selected.append(text)

        state["step"] = "reminder"

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=reminder_message(
                    selected
                ),
                quick_reply=reminder_quick_reply(),
            )
        )

        return True

    if state.get("step") == "sale_stage":

        if text not in [
            "會員預售",
            "卡友優先",
            "公售",
        ]:

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="請使用下方按鈕選擇售票階段",
                    quick_reply=simple_quick_reply([
                        ("會員預售", "會員預售"),
                        ("卡友優先", "卡友優先"),
                        ("公售", "公售"),
                        ("❌ 取消", "取消"),
                    ])
                )
            )

            return True

        show = next(
            (
                item
                for item in load_data()
                if item["id"] == state["show_id"]
            ),
            None,
        )

        if show is None:
            clear_state(user_id)
            return True

        old_value = show.get("售票階段") or ""

        show["售票階段"] = text

        update_show(show)

        clear_state(user_id)

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=(
                    "✅ 修改成功\n"
                    "──────────\n"
                    f"🎤 {show.get('藝人','')}\n"
                    f"🏷️ {show.get('活動','')}\n"
                    + (
                        f"✨ {show.get('活動名稱')}\n"
                        if show.get("活動名稱")
                        else ""
                    )
                    + "──────────\n"
                    "✏️ 售票階段\n"
                    f"🔸 原本：{old_value or '無'}\n"
                    f"🔹 修改後：{text}"
                )
            )
        )

        return True

    if state.get("step") == "value":

        field = state["field"]

        show = next(
            (
                item
                for item in load_data()
                if item["id"] == state["show_id"]
            ),
            None
        )

        if show is None:

            clear_state(user_id)

            config.line_bot_api.reply_message(
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

            elif field == "會員資訊":

                if text == "清除":
                    new_value = ""
                else:
                    new_value = text


            elif field == "售票網址":

                if text == "清除":
                    new_value = ""
                else:
                    new_value = text


            elif field == "備註":

                if text == "清除":
                    new_value = ""
                else:
                    new_value = text

            else:

                new_value = text

            old_value = show.get(field) or ""

            show[field] = new_value

            if field in {"演出日期", "搶票時間"}:

                show["提醒"]["前一天"] = False
                show["提醒"]["30分鐘"] = False
                show["提醒"]["10分鐘"] = False

            if field == "演出日期":

                show["提醒"]["演出日"] = False

                if show.get("取票日期"):
                    show["提醒"]["取票"] = False

            update_show(show)

        except ValueError:

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=(
                        "❌ 格式不正確，請重新輸入\n\n"
                        "輸入「取消」可取消修改"
                    )
                )
            )

            return True

        except Exception as e:

            print("修改演出失敗：", repr(e), flush=True)

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"❌ 修改失敗\n{e}"
                )
            )

            return True

        clear_state(user_id)

        if field == "演出日期":

            old_value = format_show_dates(old_value)
            display_value = format_show_dates(new_value)

        else:

            old_value = old_value or "無"
            display_value = new_value or "無"

        header = (
            "✅ 修改成功\n"
            "──────────\n"
            f"🎤 {show.get('藝人', '')}\n"
            f"🏷️ {show.get('活動', '')}\n"
        )

        if show.get("活動名稱"):
            header += f"✨ {show['活動名稱']}\n"

        header += "──────────\n"

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=(
                    header
                    + f"✏️ {field}\n"
                    + f"🔸 原本：{old_value}\n"
                    + f"🔹 修改後：{display_value}"
                )
            )
        )

        return True

    clear_state(user_id)

    config.line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text="❌ 修改狀態異常，請重新操作"
        )
    )

    return True
