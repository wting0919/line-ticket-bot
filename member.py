from linebot.models import TextSendMessage

from data import (
    supabase,
)

import config


# =====================
# 登記成員
# =====================

def handle_register_member(
    event,
    text,
    user_id,
):

    nickname = text.replace(
        "登記",
        ""
    ).strip()

    if not nickname:

        reply = "請輸入：\n登記 暱稱"

    else:

        try:

            supabase.table("members").upsert(
                {
                    "name": nickname,
                    "user_id": user_id,
                },
                on_conflict="user_id",
            ).execute()

        except Exception as e:

            print(
                "登記成員錯誤：",
                repr(e),
                flush=True,
            )

            reply = f"❌ 登記失敗\n{e}"

        else:

            reply = (
                "✅ 已完成登記\n"
                "──────────\n"
                f"👤 {nickname}"
            )

    config.line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=reply,
        ),
    )

    return True