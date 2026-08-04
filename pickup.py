from helpers import (
    get_state,
)

from linebot.models import TextSendMessage

from data import (
    load_data,
    update_show,
)

from show_list import (
    get_pickup_shows,
)

import config


# =====================
# 完成取票
# =====================

def handle_complete_pickup(
    event,
    text,
    user_id,
):

    state = get_state(user_id)

    if isinstance(state, dict) and "shows" in state:

        pickup_list = state["shows"]

    else:

        pickup_list = get_pickup_shows()

    try:

        show_id = int(
            text.replace(
                "完成取票ID",
                ""
            ).strip()
        )

    except ValueError:

        reply = (
            "請輸入格式：\n"
            "完成取票ID 1"
        )

    else:

        target = next(
            (
                item
                for item in pickup_list
                if item.get("id") == show_id
            ),
            None,
        )

        if target is None:

            reply = "❌ 找不到這筆取票資料"

        else:

            shows = load_data()

            show = next(
                (
                    item
                    for item in shows
                    if item["id"] == show_id
                ),
                None,
            )

            if show is None:

                reply = "❌ 找不到這筆演出"

            elif show.get("取票狀態") == "已取票":

                reply = "⚠️ 這筆演出已經完成取票"

            else:

                show["取票狀態"] = "已取票"

                try:

                    update_show(show)

                except Exception as e:

                    print(
                        "完成取票更新錯誤：",
                        repr(e),
                        flush=True,
                    )

                    reply = f"❌ 更新失敗\n{e}"

                else:

                    reply = (
                        "✅ 已完成取票\n"
                        "──────────\n"
                        f"🎤 {show['演出名稱']}\n"
                        f"🎫 取票人：{show.get('取票人') or '未設定'}\n"
                        "──────────\n"
                        "✅ 已取票"
                    )

    config.line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=reply
        )
    )

    return True