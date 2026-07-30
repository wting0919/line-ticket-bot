user_state = {}
line_bot_api = None

get_all_shows = None

from linebot.models import TextSendMessage

from data import (
    load_data,
    update_show,
    load_members,
)

from ui import (
    member_quick_reply,
)

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

