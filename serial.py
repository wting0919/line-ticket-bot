from linebot.models import TextSendMessage

from data import (
    update_show,
)

from show_list import (
    get_all_shows,
)

from mention import (
    push_mention_message,
)

line_bot_api = None
GROUP_ID = None


# =====================
# 序號提醒
# =====================

def handle_serial_number(
    event,
    text,
):

    shows = get_all_shows()

    try:

        lines = text.split("\n")

        index = int(
            lines[0]
            .replace(
                "序號",
                ""
            )
            .strip()
        ) - 1

        if index < 0 or index >= len(shows):

            reply = "❌ 找不到這筆演出"

        else:

            show = shows[index]

            for line in lines[1:]:

                if line.startswith("取票序號："):

                    show["取票序號"] = (
                        line
                        .replace(
                            "取票序號：",
                            ""
                        )
                        .strip()
                    )

            update_show(show)

            notify_message = (
                "🎫 序號已出來！\n\n"
                f"🎤 {show['演出名稱']}\n\n"
                f"🎟 序號：\n"
                f"{show.get('取票序號','')}\n\n"
                f"👤 搶票大師：\n"
                f"{show.get('搶票大師','未設定')}\n\n"
                f"👥 取票人：\n"
                f"{show.get('取票人') or '未設定'}\n\n"
                "請確認取票資訊～"
            )

            mention_names = []

            if show.get("搶票大師"):
                mention_names.append(show["搶票大師"])

            mention_names.extend(
                [
                    x.strip()
                    for x in show.get("取票人", "").split("、")
                    if x.strip()
                ]
            )

            push_mention_message(
                GROUP_ID,
                notify_message,
                mention_names,
            )

            reply = "✅ 已發送序號提醒"

    except Exception as e:

        print("序號提醒錯誤：", e)

        reply = (
            "請輸入格式：\n"
            "序號 1\n"
            "取票序號：A123456"
        )

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=reply
        )
    )

    return True