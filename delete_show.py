from linebot.models import TextSendMessage

from data import (
    supabase,
)

from show_list import (
    get_all_shows,
)

from helpers import (
    get_state,
)

from utils import (
    format_show_dates,
)

import config


# =====================
# 刪除功能
# =====================

def handle_delete_show(
    event,
    text,
    user_id,
):

    state = get_state(user_id)

    if isinstance(state, dict) and "shows" in state:

        target_list = state["shows"]

    else:

        target_list = get_all_shows()

    try:

        index = int(
            text.replace(
                "刪除",
                ""
            ).strip()
        ) - 1

    except ValueError:

        reply = (
            "請輸入格式：\n"
            "刪除 1"
        )

    else:

        if index < 0 or index >= len(target_list):

            reply = "❌ 找不到這筆演出"

        else:

            target = target_list[index]

            try:

                supabase.table("shows") \
                    .delete() \
                    .eq(
                        "id",
                        target["id"]
                    ) \
                    .execute()

            except Exception as e:

                print(
                    "刪除失敗：",
                    repr(e),
                    flush=True,
                )

                reply = f"❌ 刪除失敗\n{e}"

            else:

                reply = (
                    "✅ 已刪除演出\n"
                    "──────────\n"
                    f"🎤 {target['演出名稱']}\n"
                    f"📅 {format_show_dates(target['演出日期'])}"
                )

    config.line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=reply
        )
    )

    return True