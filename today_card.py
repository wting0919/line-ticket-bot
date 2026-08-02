from datetime import datetime

from linebot.models import FlexSendMessage

from show_list import (
    get_waiting_shows,
    get_pickup_shows,
    get_all_shows,
)

from utils import (
    parse_datetime,
    parse_date,
    format_datetime,
    format_show_dates_inline,
)

# =====================
# Color
# =====================

HEADER_COLOR = "#C9B29B"

BODY_COLOR = "#FFFCF8"

TEXT_COLOR = "#5C5148"

SUBTEXT_COLOR = "#75695F"

LINE_COLOR = "#E7DDD2"

BUTTON_COLOR = "#B99F86"


def build_header(today):

    return {
        "type": "box",
        "layout": "vertical",
        "backgroundColor": HEADER_COLOR,
        "paddingTop": "12px",
        "paddingBottom": "12px",
        "paddingStart": "18px",
        "paddingEnd": "18px",
        "contents": [

            {
                "type": "text",
                "text": "☀️ 今日待辦事項",
                "weight": "bold",
                "size": "lg",
                "color": "#FFFFFF"
            },

            {
                "type": "text",
                "text": today.strftime("%Y/%m/%d"),
                "size": "xs",
                "margin": "sm",
                "color": "#F8F5F2"
            }

        ]
    }


def build_today_card():

    today = datetime.now().date()

    ticket_today = [
        show
        for show in get_waiting_shows()
        if parse_datetime(show.get("搶票時間")).date() == today
    ]

    pickup_today = [
        show
        for show in get_pickup_shows()
        if parse_date(show.get("取票日期")).date() == today
    ]

    show_today = [
        show
        for show in get_all_shows()
        if today
        in [
            parse_date(d).date()
            for d in show["演出日期"].split("、")
        ]
    ]

    body = []

    body.append(
        {
            "type": "text",
            "text": f"📅 {today.strftime('%Y/%m/%d')}",
            "size": "sm",
            "color": "#888888",
        }
    )

    body.append(
        {
            "type": "separator",
            "margin": "lg",
        }
    )

    # 搶票
    body.append(
        {
            "type": "text",
            "text": f"🎟 今日搶票（{len(ticket_today)}）",
            "weight": "bold",
            "margin": "lg",
        }
    )

    if ticket_today:

        for show in ticket_today:

            body.extend(
                [
                    {
                        "type": "text",
                        "text": show["演出名稱"],
                        "weight": "bold",
                        "margin": "md",
                    },
                    {
                        "type": "text",
                        "text": f"🕒 {format_datetime(show['搶票時間'])}",
                        "size": "sm",
                        "color": "#666666",
                    },
                ]
            )

    else:

        body.append(
            {
                "type": "text",
                "text": "今天沒有搶票",
                "size": "sm",
                "color": "#888888",
            }
        )

    body.append(
        {
            "type": "separator",
            "margin": "lg",
        }
    )

    # 取票
    body.append(
        {
            "type": "text",
            "text": f"📦 今日取票（{len(pickup_today)}）",
            "weight": "bold",
            "margin": "lg",
        }
    )

    if pickup_today:

        for show in pickup_today:

            body.extend(
                [
                    {
                        "type": "text",
                        "text": show["演出名稱"],
                        "weight": "bold",
                        "margin": "md",
                    },
                    {
                        "type": "text",
                        "text": f"👤 {show.get('取票人') or '未設定'}",
                        "size": "sm",
                        "color": "#666666",
                    },
                ]
            )

    else:

        body.append(
            {
                "type": "text",
                "text": "今天沒有取票",
                "size": "sm",
                "color": "#888888",
            }
        )

    body.append(
        {
            "type": "separator",
            "margin": "lg",
        }
    )

    # 演出
    body.append(
        {
            "type": "text",
            "text": f"🎤 今日演出（{len(show_today)}）",
            "weight": "bold",
            "margin": "lg",
        }
    )

    if show_today:

        for show in show_today:

            body.extend(
                [
                    {
                        "type": "text",
                        "text": show["演出名稱"],
                        "weight": "bold",
                        "margin": "md",
                    },
                    {
                        "type": "text",
                        "text": format_show_dates_inline(show["演出日期"]),
                        "size": "sm",
                        "color": "#666666",
                        "wrap": True,
                    },
                ]
            )

    else:

        body.append(
            {
                "type": "text",
                "text": "今天沒有演出",
                "size": "sm",
                "color": "#888888",
            }
        )

    return FlexSendMessage(
        alt_text="今日任務",
        contents={
            "type": "bubble",
            "header": build_header(today),
                "contents": [
                    {
                        "type": "text",
                        "text": "☀️ 今日任務",
                        "weight": "bold",
                        "size": "xl",
                        "color": "#FFFFFF",
                        "align": "center",
                    }
                ],
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": body,
            },
            "footer": {
                "type": "box",
                "layout": "horizontal",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {
                            "type": "message",
                            "label": "🎟",
                            "text": "搶票列表",
                        },
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {
                            "type": "message",
                            "label": "📦",
                            "text": "取票列表",
                        },
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {
                            "type": "message",
                            "label": "📋",
                            "text": "演出列表",
                        },
                    },
                ],
            },
        },
    )