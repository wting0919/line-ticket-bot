from linebot.models import TextSendMessage

from data import (
    supabase,
)

line_bot_api = None


def handle_register_member(
    event,
    text,
    user_id,
):

    nickname = text.replace(
        "登記 ",
        ""
    ).strip()

    if not nickname:

        reply = "請輸入：登記 暱稱"

    else:

        supabase.table("members").upsert(
            {
                "name": nickname,
                "user_id": user_id,
            },
            on_conflict="user_id",
        ).execute()

        reply = (
            "✅ 登記成功\n\n"
            f"暱稱：{nickname}\n"
            f"ID：{user_id}"
        )

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=reply,
        ),
    )

    return True