from linebot.models import TextSendMessage

from data import (
    supabase,
)

from show_list import (
    get_all_shows,
)

user_state = {}
line_bot_api = None


# =====================
# 刪除功能
# =====================

def handle_delete_show(
    event,
    text,
    user_id,
):

    try:

        index = int(
            text.replace(
                "刪除",
                ""
            ).strip()
        ) - 1

        state = user_state.get(user_id)

        if isinstance(state, dict) and "shows" in state:

            target_list = state["shows"]

        else:

            target_list = get_all_shows()

        if index < 0 or index >= len(target_list):

            reply = "❌ 找不到這筆演出"

        else:

            target = target_list[index]

            supabase.table("shows") \
                .delete() \
                .eq(
                    "id",
                    target["id"]
                ) \
                .execute()

            reply = (
                "✅ 刪除成功\n\n"
                f"🎤 {target['演出名稱']}\n"
                f"📅 演出日期：{target['演出日期']}"
            )

    except Exception as e:

        print("刪除錯誤：", e)

        reply = (
            "請輸入格式：\n"
            "刪除 1"
        )

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=reply
        )
    )

    return True