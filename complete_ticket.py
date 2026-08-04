from linebot.models import TextSendMessage

from data import (
    load_data,
    update_show,
    load_members,
)

from ui import (
    member_quick_reply,
)

from show_list import (
    get_all_shows,
)

from helpers import (
    get_state,
    clear_state,
    set_state,
)

import config


DEFAULT_COMPLETE_DATA = {
    "搶票大師": "",
    "取票人": [],
}


# =====================
# 完成搶票
# =====================

def handle_complete_ticket(event, text, user_id):

    state = get_state(user_id)

    if isinstance(state, dict) and "shows" in state:

        shows = state["shows"]

    else:

        shows = get_all_shows()

    try:

        show_id = int(
            text.replace("完成搶票ID", "").strip()
        )

    except Exception:

        return TextSendMessage(
            text="請輸入：\n完成搶票ID 1"
        )

    show = next(
        (
            item
            for item in shows
            if item.get("id") == show_id
        ),
        None,
    )

    if show is None:

        return TextSendMessage(
            text="❌ 找不到這筆演出"
        )

    if show.get("搶票狀態") == "已搶票":

        return TextSendMessage(
            text="⚠️ 這筆演出已經完成搶票"
        )

    set_state(
        user_id,
        {
            "mode": "完成搶票",
            "step": "master",
            "show_id": show["id"],
            "data": DEFAULT_COMPLETE_DATA.copy(),
        }
    )

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


# =====================
# 成員選單
# =====================

def send_member_picker(
    event,
    title,
    selected=None,
    allow_finish=False,
    allow_skip=True,
):

    selected = selected or []

    if selected:

        selected_text = "、".join(selected)

        message = (
            f"{title}\n\n"
            f"已選擇：{selected_text}"
        )

    else:

        message = (
            f"{title}\n\n"
            "已選擇：無"
        )

    config.line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=message,
            quick_reply=member_quick_reply(
                selected=selected,
                allow_finish=allow_finish,
                allow_skip=allow_skip,
            ),
        ),
    )

# =====================
# 完成搶票問答流程
# =====================

def handle_complete_ticket_flow(event, text, user_id):

    state = get_state(user_id)

    if not isinstance(state, dict):
        return False

    if state.get("mode") != "完成搶票":
        return False

    if text == "取消":

        clear_state(user_id)

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="已取消完成搶票"
            )
        )

        return True

    data = state["data"]

    # =====================
    # 第一步：選擇搶票大師
    # =====================

    if state.get("step") == "master":

        if text == "略過":

            data["搶票大師"] = ""

        else:

            members = load_members()

            if text not in members:

                config.line_bot_api.reply_message(
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

            data["搶票大師"] = text

        state["step"] = "people"

        send_member_picker(
            event=event,
            title="請選擇取票人",
            selected=data["取票人"],
            allow_finish=True,
            allow_skip=True,
        )

        return True

    # =====================
    # 第二步：多選取票人
    # =====================

    if state.get("step") == "people":

        selected_people = data["取票人"]

        if text == "略過":

            selected_people.clear()

            return finish_complete_ticket(
                event,
                user_id,
                state,
            )

        if text == "完成":

            return finish_complete_ticket(
                event,
                user_id,
                state,
            )

        members = load_members()

        if text not in members:

            send_member_picker(
                event=event,
                title="請使用下方按鈕選擇取票人",
                selected=selected_people,
                allow_finish=True,
                allow_skip=True,
            )

            return True

        if text not in selected_people:
            selected_people.append(text)

        send_member_picker(
            event=event,
            title="請繼續選擇取票人，選好後按「完成」",
            selected=selected_people,
            allow_finish=True,
            allow_skip=False,
        )

        return True

    clear_state(user_id)

    config.line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text="❌ 操作已失效，請重新執行「完成搶票」"
        )
    )

    return True


def finish_complete_ticket(
    event,
    user_id,
    state,
):

    shows = load_data()

    show = next(
        (item for item in shows if item["id"] == state["show_id"]),
        None,
    )

    if show is None:

        clear_state(user_id)

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="❌ 操作已失效，請重新執行「完成搶票」"
            )
        )

        return True

    data = state["data"]

    show["搶票大師"] = data["搶票大師"]
    show["取票人"] = "、".join(data["取票人"])
    show["搶票狀態"] = "已搶票"

    try:

        update_show(show)

    except Exception as e:

        print(
            "完成搶票更新錯誤：",
            repr(e),
            flush=True,
        )

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=f"❌ 更新失敗\n{e}"
            )
        )

        return True

    clear_state(user_id)

    config.line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=(
                "✅ 已完成搶票\n"
                "──────────\n"
                f"🎤 {show['演出名稱']}\n"
                f"🎯 搶票大師：{show['搶票大師'] or '未設定'}\n"
                f"🎫 取票人：{show['取票人'] or '未設定'}\n"
                "──────────\n"
                "✅ 已搶票"
            )
        )
    )

    return True

def handle_ticket_failed(event, text, user_id):

    state = get_state(user_id)

    if isinstance(state, dict) and "shows" in state:

        shows = state["shows"]

    else:

        shows = get_all_shows()

    try:
        show_id = int(
            text.replace("未搶到ID", "").strip()
        )

    except Exception:

        return TextSendMessage(
            text="請輸入：\n未搶到ID 1"
        )

    show = next(
        (
            item
            for item in shows
            if item.get("id") == show_id
        ),
        None,
    )

    if show is None:

        return TextSendMessage(
            text="❌ 找不到這筆演出"
        )

    if show.get("搶票狀態") == "已搶票":

        return TextSendMessage(
            text="⚠️ 這筆演出已經完成搶票"
        )

    show["搶票狀態"] = "未搶到"

    try:

        update_show(show)

    except Exception as e:

        return TextSendMessage(
            text=f"❌ 更新失敗\n{e}"
        )

    return TextSendMessage(
        text=(
            "❌ 已標記為未搶到\n"
            "──────────\n"
            f"🎤 {show['演出名稱']}\n"
            "❌ 未搶到"
        )
    )