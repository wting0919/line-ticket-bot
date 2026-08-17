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

import config


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

    except ValueError:

        reply = (
            "請輸入格式：\n"
            "序號 1\n"
            "取票序號：A123456"
        )

    else:

        if index < 0 or index >= len(shows):

            reply = "❌ 找不到這筆演出"

        else:

            show = shows[index]

            serial = ""

            for line in lines[1:]:

                if line.startswith("取票序號："):

                    serial = (
                        line.replace(
                            "取票序號：",
                            ""
                        ).strip()
                    )

            if not serial:

                reply = "❌ 請輸入取票序號"

            else:

                show["取票序號"] = serial

                try:

                    update_show(show)

                except Exception as e:

                    print(
                        "更新序號失敗：",
                        repr(e),
                        flush=True,
                    )

                    reply = f"❌ 更新失敗\n{e}"

                else:

                    title = "｜".join(
                        part
                        for part in [
                            show.get("藝人", ""),
                            show.get("活動", ""),
                            show.get("活動名稱", ""),
                        ]
                        if part
                    )

                    notify_message = (
                        "🎫 取票序號通知\n"
                        "──────────\n"
                        f"🎤 {title}\n"
                        f"🎟 序號：{show['取票序號']}\n"
                        "──────────\n"
                        f"🎯 搶票大師：{show.get('搶票大師') or '未設定'}\n"
                        f"👤 取票人員：{show.get('取票人') or '未設定'}\n"
                        "──────────\n"
                        "請確認取票資訊～"
                    )

                    mention_names = []

                    if show.get("搶票大師"):

                        mention_names.append(
                            show["搶票大師"]
                        )

                    mention_names.extend(
                        [
                            x.strip()
                            for x in show.get(
                                "取票人",
                                ""
                            ).split("、")
                            if x.strip()
                        ]
                    )

                    try:

                        push_mention_message(
                            config.GROUP_ID,
                            notify_message,
                            mention_names,
                        )

                    except Exception as e:

                        print(
                            "序號提醒失敗：",
                            repr(e),
                            flush=True,
                        )

                        reply = (
                            f"❌ 發送提醒失敗\n{e}"
                        )

                    else:

                        reply = (
                            "✅ 已發送取票序號提醒"
                        )

    config.line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=reply
        )
    )

    return True