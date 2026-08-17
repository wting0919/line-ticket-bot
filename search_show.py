from datetime import datetime

from linebot.models import TextSendMessage

from show_list import get_all_shows

from utils import (
    format_show_dates,
    format_ticket_status,
    LIST_FOOTER,
)

from helpers import (
    set_show_list,
)

from ui import (
    list_reply,
)

import config

# 關鍵字別名

KEYWORD_ALIAS = {

    # 團體
    "svt": "seventeen",
    "十七": "seventeen",

    "大棒": "bigbang",
    "bb": "bigbang",

    # 售票平台
    "拓": "拓元",
    "kk": "kktix",

    # 狀態
    "待搶": "待搶票",
    "等待搶票": "待搶票",
    "已搶": "已搶票",
    "未搶": "未搶到",
    "未取": "未取票",
    "已取": "已取票",
}


def handle_search_show(event, text, user_id):

    keyword = text.replace("搜尋", "").strip()

    keyword = KEYWORD_ALIAS.get(
        keyword.lower(),
        keyword
    )

    keyword_lower = str(keyword).lower()

    if not keyword:

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=(
                    "請輸入搜尋條件\n\n"
                    "例如：\n"
                    "搜尋 BIGBANG\n"
                    "搜尋 演唱會\n"
                    "搜尋 拓元\n"
                    "搜尋 10月\n"
                    "搜尋 待搶票"
                )
            )
        )
        return True

    shows = get_all_shows()

    today = datetime.now()

    results = []

    for show in shows:

        name = " ".join([
            str(show.get("藝人", "")),
            str(show.get("活動", "")),
            str(show.get("活動名稱", "")),
        ])
        date = str(show.get("演出日期", ""))
        platform = str(show.get("售票平台", ""))
        ticket = str(show.get("搶票狀態", ""))
        pickup = str(show.get("取票狀態", ""))
        note = str(show.get("備註", ""))

        matched = False

        # ===== 今天 =====
        if keyword in ("今天", "今日"):

            matched = date.startswith(today.strftime("%Y/%m/%d"))

        # ===== 本月 =====
        elif keyword == "本月":

            matched = date.startswith(today.strftime("%Y/%m"))

        # ===== 月份 =====
        elif keyword.endswith("月"):

            try:

                month = int(keyword.replace("月", ""))

                matched = f"/{month:02d}/" in date

            except ValueError:

                pass

        # ===== 狀態 =====
        elif keyword in (
            "待搶",
            "待搶票",
            "等待搶票",
        ):

            matched = ticket == "待搶票"

        elif keyword in (
            "已搶",
            "已搶票",
        ):

            matched = ticket == "已搶票"

        elif keyword in (
            "未搶",
            "未搶到",
        ):

            matched = ticket == "未搶到"

        elif keyword in (
            "未取",
            "未取票",
        ):

            matched = pickup == "未取票"

        elif keyword in (
            "已取",
            "已取票",
        ):

            matched = pickup == "已取票"

        # ===== 一般模糊搜尋 =====
        else:

            content = " ".join([
                name,
                date,
                platform,
                ticket,
                pickup,
                member,
                note,
            ]).lower()

            matched = (
                keyword_lower in content
            )

        if matched:

            results.append(show)

    if not results:

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=f"找不到「{keyword}」相關演出"
            )
        )
        return True

    reply = f"🔍 搜尋結果（{len(results)}）"

    for i, show in enumerate(results, start=1):

        ticket_status = format_ticket_status(
            show.get("搶票狀態", "待搶票")
        )

        reply += (
            "\n──────────\n"
            artist = show.get("藝人", "")
            activity = show.get("活動", "")
            activity_name = show.get("活動名稱", "")

            title = "｜".join(
                part for part in [
                    artist,
                    activity,
                    activity_name,
                ]
                if part
            )

            f"{i}. 🎤 {title or '未命名演出'}\n"
            f"📅 {format_show_dates(show.get('演出日期', ''))}\n"
            f"{ticket_status}"
        )

    reply += LIST_FOOTER

    set_show_list(
        user_id,
        "搜尋",
        results,
    )

    if len(results) > 10:

        reply += (
            "\n──────────\n"
            "💡 第 11 筆以上請輸入：查看 編號"
        )

    config.line_bot_api.reply_message(
        event.reply_token,
        list_reply(
            reply,
            len(results)
        )
    )