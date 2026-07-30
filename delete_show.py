from linebot.models import TextSendMessage

from data import (
    supabase,
)

from show_list import (
    get_waiting_shows,
    get_pickup_shows,
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

        if user_state.get(user_id) == "搶票列表":

            target_list = get_waiting_shows()

        elif user_state.get(user_id) == "取票列表":

            target_list = get_pickup_shows()

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