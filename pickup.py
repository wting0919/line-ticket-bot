from linebot.models import TextSendMessage

from data import (
    load_data,
    update_show,
)

from show_list import (
    get_pickup_shows,
)

line_bot_api = None


# =====================
# 完成取票
# =====================

def handle_complete_pickup(
    event,
    text,
):

    pickup_list = get_pickup_shows()

    try:

        index = int(
            text.replace(
                "完成取票",
                ""
            ).strip()
        ) - 1

        if index < 0 or index >= len(pickup_list):

            reply = "❌ 找不到這筆取票資料"

        else:

            target = pickup_list[index]

            shows = load_data()

            show = next(
                (
                    item
                    for item in shows
                    if item["id"] == target["id"]
                ),
                None,
            )

            if not show:

                reply = "❌ 找不到這筆演出"

            else:

                show["取票狀態"] = "已取票"

                update_show(show)

                reply = (
                    "✅ 已完成取票\n\n"
                    f"🎤 {target['演出名稱']}\n"
                    f"📅 演出日期：{target['演出日期']}\n"
                    "🎫 狀態：已取票"
                )

    except Exception as e:

        print("完成取票錯誤：", e)

        reply = (
            "請輸入格式：\n"
            "完成取票 1"
        )

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=reply
        )
    )

    return True