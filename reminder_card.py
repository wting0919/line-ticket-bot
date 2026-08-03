from linebot.models import FlexSendMessage

from utils import (
    format_price,
    format_show_dates,
    parse_date,
    parse_datetime,
)


# =========================================================
# Reminder Card V2
# 奶茶色系
# =========================================================

HEADER_COLOR = "#C9B29B"
URGENT_HEADER_COLOR = "#B56C55"

BODY_COLOR = "#FFFCF8"
SECTION_COLOR = "#F4ECE4"

TEXT_COLOR = "#5C5148"
SUBTEXT_COLOR = "#75695F"
LIGHT_TEXT_COLOR = "#9A8D82"

LINE_COLOR = "#E7DDD2"
BUTTON_COLOR = "#B99F86"

WHITE_COLOR = "#FFFFFF"
HEADER_SUBTEXT_COLOR = "#FFF9F3"

WAITING_BACKGROUND_COLOR = "#FFF4D6"
WAITING_TEXT_COLOR = "#A87300"

SUCCESS_BACKGROUND_COLOR = "#E8F3E6"
SUCCESS_TEXT_COLOR = "#5B7D4A"


WEEKDAY_TEXT = [
    "一",
    "二",
    "三",
    "四",
    "五",
    "六",
    "日",
]


# =========================================================
# 基本工具
# =========================================================

def safe_text(
    value,
    default="未設定",
):
    if value is None:
        return default

    text = str(value).strip()

    return text if text else default


def remove_none_elements(value):
    """
    避免 Flex contents 出現 null。
    """

    if isinstance(value, list):
        return [
            remove_none_elements(item)
            for item in value
            if item is not None
        ]

    if isinstance(value, dict):
        return {
            key: remove_none_elements(item)
            for key, item in value.items()
            if item is not None
        }

    return value


def build_separator(
    margin="lg",
):
    return {
        "type": "separator",
        "margin": margin,
        "color": LINE_COLOR,
    }


def format_datetime_with_weekday(value):
    """
    2026/08/15（六）13:00
    """

    if not value:
        return "未設定"

    parsed_value = parse_datetime(value)

    if parsed_value is None:
        return safe_text(value)

    weekday = WEEKDAY_TEXT[
        parsed_value.weekday()
    ]

    return (
        f"{parsed_value.strftime('%Y/%m/%d')}"
        f"（{weekday}）"
        f"{parsed_value.strftime('%H:%M')}"
    )


def format_date_with_weekday(value):
    """
    2026/10/10（六）
    """

    if not value:
        return "未設定"

    parsed_value = parse_date(value)

    if parsed_value is None:
        return safe_text(value)

    if hasattr(parsed_value, "date"):
        date_value = parsed_value.date()
    else:
        date_value = parsed_value

    weekday = WEEKDAY_TEXT[
        date_value.weekday()
    ]

    return (
        f"{date_value.strftime('%Y/%m/%d')}"
        f"（{weekday}）"
    )


def format_ticket_clock(value):
    """
    13:00
    """

    parsed_value = parse_datetime(value)

    if parsed_value is None:
        return "--:--"

    return parsed_value.strftime("%H:%M")


def format_ticket_date(value):
    """
    2026/08/15（六）
    """

    parsed_value = parse_datetime(value)

    if parsed_value is None:
        return "日期未設定"

    weekday = WEEKDAY_TEXT[
        parsed_value.weekday()
    ]

    return (
        f"{parsed_value.strftime('%Y/%m/%d')}"
        f"（{weekday}）"
    )


# =========================================================
# 狀態膠囊
# =========================================================

def build_status_tag(
    text,
    background_color,
    text_color,
):
    return {
        "type": "box",
        "layout": "vertical",
        "backgroundColor": background_color,
        "cornerRadius": "12px",
        "paddingTop": "7px",
        "paddingBottom": "7px",
        "paddingStart": "12px",
        "paddingEnd": "12px",
        "contents": [
            {
                "type": "text",
                "text": text,
                "size": "xxs",
                "weight": "bold",
                "color": text_color,
                "align": "center",
                "wrap": False,
            }
        ],
    }


def build_waiting_tag(text):
    return build_status_tag(
        text=text,
        background_color=WAITING_BACKGROUND_COLOR,
        text_color=WAITING_TEXT_COLOR,
    )


def build_success_tag(text):
    return build_status_tag(
        text=text,
        background_color=SUCCESS_BACKGROUND_COLOR,
        text_color=SUCCESS_TEXT_COLOR,
    )


def build_status_area(tags):
    return {
        "type": "box",
        "layout": "horizontal",
        "spacing": "sm",
        "contents": tags,
    }


# =========================================================
# 資訊元件
# =========================================================

def build_info_row(
    icon,
    label,
    value,
    margin="sm",
):
    return {
        "type": "box",
        "layout": "horizontal",
        "margin": margin,
        "alignItems": "flex-start",
        "contents": [
            {
                "type": "text",
                "text": icon,
                "size": "sm",
                "flex": 0,
            },
            {
                "type": "text",
                "text": label,
                "size": "xs",
                "weight": "bold",
                "color": SUBTEXT_COLOR,
                "margin": "sm",
                "flex": 3,
                "wrap": True,
            },
            {
                "type": "text",
                "text": safe_text(value),
                "size": "xs",
                "color": TEXT_COLOR,
                "flex": 6,
                "wrap": True,
            },
        ],
    }


def build_note(note):
    if not note:
        return None

    return {
        "type": "box",
        "layout": "vertical",
        "margin": "lg",
        "paddingAll": "12px",
        "backgroundColor": SECTION_COLOR,
        "cornerRadius": "10px",
        "contents": [
            {
                "type": "text",
                "text": "📝 備註",
                "size": "xs",
                "weight": "bold",
                "color": SUBTEXT_COLOR,
            },
            {
                "type": "text",
                "text": safe_text(note, "無"),
                "size": "sm",
                "color": TEXT_COLOR,
                "margin": "sm",
                "wrap": True,
            },
        ],
    }


def build_time_focus(
    ticket_time,
    urgent=False,
):
    return {
        "type": "box",
        "layout": "vertical",
        "margin": "lg",
        "paddingTop": "10px",
        "paddingBottom": "10px",
        "contents": [
            {
                "type": "text",
                "text": format_ticket_clock(
                    ticket_time
                ),
                "size": "3xl",
                "weight": "bold",
                "color": (
                    URGENT_HEADER_COLOR
                    if urgent
                    else TEXT_COLOR
                ),
                "align": "center",
            },
            {
                "type": "text",
                "text": format_ticket_date(
                    ticket_time
                ),
                "size": "xs",
                "color": SUBTEXT_COLOR,
                "align": "center",
                "margin": "sm",
                "wrap": True,
            },
        ],
    }


def build_milk_tea_divider():
    return {
        "type": "box",
        "layout": "horizontal",
        "margin": "md",
        "contents": [
            {
                "type": "box",
                "layout": "vertical",
                "width": "80px",
                "height": "4px",
                "backgroundColor": BUTTON_COLOR,
                "cornerRadius": "2px",
                "contents": [],
            }
        ],
    }


# =========================================================
# 查看這一筆詳細資料
# =========================================================

def build_detail_button(show):
    """
    直接用 Supabase id 開啟這一筆。
    """

    show_id = safe_text(
        show.get("id"),
        "",
    )

    return {
        "type": "box",
        "layout": "vertical",
        "backgroundColor": BUTTON_COLOR,
        "cornerRadius": "10px",
        "paddingTop": "11px",
        "paddingBottom": "11px",
        "action": {
            "type": "message",
            "label": "🔍 查看詳細",
            "text": f"查看ID {show_id}",
        },
        "contents": [
            {
                "type": "text",
                "text": "🔍 查看詳細",
                "size": "sm",
                "weight": "bold",
                "color": WHITE_COLOR,
                "align": "center",
            }
        ],
    }


# =========================================================
# 通用 Bubble
# =========================================================

def build_reminder_bubble(
    show,
    header_title,
    header_subtitle,
    body_contents,
    alt_text,
    urgent=False,
):
    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": (
                URGENT_HEADER_COLOR
                if urgent
                else HEADER_COLOR
            ),
            "paddingTop": "16px",
            "paddingBottom": "16px",
            "paddingStart": "18px",
            "paddingEnd": "18px",
            "contents": [
                {
                    "type": "text",
                    "text": header_title,
                    "size": "xl",
                    "weight": "bold",
                    "color": WHITE_COLOR,
                    "wrap": True,
                },
                {
                    "type": "text",
                    "text": header_subtitle,
                    "size": "xs",
                    "color": HEADER_SUBTEXT_COLOR,
                    "margin": "sm",
                    "wrap": True,
                },
            ],
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": BODY_COLOR,
            "paddingTop": "16px",
            "paddingBottom": "16px",
            "paddingStart": "16px",
            "paddingEnd": "16px",
            "contents": body_contents,
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": BODY_COLOR,
            "paddingTop": "4px",
            "paddingBottom": "16px",
            "paddingStart": "16px",
            "paddingEnd": "16px",
            "contents": [
                build_detail_button(show)
            ],
        },
        "styles": {
            "header": {
                "separator": False,
            },
            "body": {
                "separator": False,
            },
            "footer": {
                "separator": False,
            },
        },
    }

    bubble = remove_none_elements(bubble)

    return FlexSendMessage(
        alt_text=alt_text,
        contents=bubble,
    )


# =========================================================
# 🎟 明日搶票
# =========================================================

def build_tomorrow_ticket_card(show):
    body_contents = [
        build_status_area([
            build_waiting_tag("待搶票")
        ]),
        {
            "type": "text",
            "text": (
                f"🎤 "
                f"{safe_text(show.get('演出名稱'), '未命名演出')}"
            ),
            "size": "md",
            "weight": "bold",
            "color": TEXT_COLOR,
            "margin": "lg",
            "wrap": True,
        },
        build_info_row(
            icon="🕒",
            label="搶票時間",
            value=format_datetime_with_weekday(
                show.get("搶票時間")
            ),
            margin="lg",
        ),
        build_note(
            show.get("備註")
        ),
    ]

    return build_reminder_bubble(
        show=show,
        header_title="🎟 明日搶票",
        header_subtitle="明天記得準時搶票！",
        body_contents=body_contents,
        alt_text="🎟 明日搶票提醒",
    )


# =========================================================
# ⏰／🚨 搶票倒數
# =========================================================

def build_ticket_countdown_card(
    show,
    minutes,
):
    urgent = minutes == 10

    body_contents = [
        build_status_area([
            build_waiting_tag("待搶票")
        ]),
        {
            "type": "text",
            "text": (
                f"🎤 "
                f"{safe_text(show.get('演出名稱'), '未命名演出')}"
            ),
            "size": "md",
            "weight": "bold",
            "color": TEXT_COLOR,
            "margin": "lg",
            "wrap": True,
        },
        build_time_focus(
            ticket_time=show.get("搶票時間"),
            urgent=urgent,
        ),
        build_separator(),
        build_info_row(
            icon="🏢",
            label="售票平台",
            value=show.get("售票平台"),
            margin="lg",
        ),
        build_info_row(
            icon="💰",
            label="價格張數",
            value=format_price(
                show.get("價格張數")
            ),
        ),
        build_note(
            show.get("備註")
        ),
    ]

    return build_reminder_bubble(
        show=show,
        header_title=(
            "🚨 還有 10 分鐘"
            if urgent
            else "⏰ 還有 30 分鐘"
        ),
        header_subtitle=(
            "準備開始搶票！"
            if urgent
            else "開始準備搶票！"
        ),
        body_contents=body_contents,
        alt_text=(
            f"🎟 搶票倒數 {minutes} 分鐘"
        ),
        urgent=urgent,
    )


# =========================================================
# 📦 取票提醒
# =========================================================

def build_pickup_reminder_card(show):
    body_contents = [
        build_status_area([
            build_waiting_tag("未取票")
        ]),
        {
            "type": "text",
            "text": (
                f"🎤 "
                f"{safe_text(show.get('演出名稱'), '未命名演出')}"
            ),
            "size": "md",
            "weight": "bold",
            "color": TEXT_COLOR,
            "margin": "lg",
            "wrap": True,
        },
        build_info_row(
            icon="📅",
            label="取票日期",
            value=format_date_with_weekday(
                show.get("取票日期")
            ),
            margin="lg",
        ),
        build_info_row(
            icon="👤",
            label="取票人員",
            value=show.get("取票人"),
        ),
        build_milk_tea_divider(),
        build_info_row(
            icon="🎯",
            label="搶票大師",
            value=show.get("搶票大師"),
            margin="md",
        ),
    ]

    return build_reminder_bubble(
        show=show,
        header_title="📦 今天記得取票",
        header_subtitle="可以取票囉！",
        body_contents=body_contents,
        alt_text="📦 取票提醒",
    )


# =========================================================
# 🎤 演出日提醒
# =========================================================

def build_show_day_reminder_card(show):
    pickup_status = show.get(
        "取票狀態",
        "未取票",
    )

    status_tags = [
        build_success_tag("已搶票")
    ]

    if pickup_status == "已取票":
        status_tags.append(
            build_success_tag("已取票")
        )
    else:
        status_tags.append(
            build_waiting_tag("未取票")
        )

    body_contents = [
        build_status_area(status_tags),
        {
            "type": "text",
            "text": (
                f"🎤 "
                f"{safe_text(show.get('演出名稱'), '未命名演出')}"
            ),
            "size": "lg",
            "weight": "bold",
            "color": TEXT_COLOR,
            "margin": "lg",
            "wrap": True,
        },
        build_info_row(
            icon="📅",
            label="演出日期",
            value=format_show_dates(
                show.get("演出日期", "")
            ),
            margin="lg",
        ),
        {
            "type": "box",
            "layout": "vertical",
            "margin": "xl",
            "paddingAll": "16px",
            "backgroundColor": SECTION_COLOR,
            "cornerRadius": "12px",
            "contents": [
                {
                    "type": "text",
                    "text": "🎉 玩得開心！",
                    "size": "lg",
                    "weight": "bold",
                    "color": SUCCESS_TEXT_COLOR,
                    "align": "center",
                }
            ],
        },
    ]

    return build_reminder_bubble(
        show=show,
        header_title="🎤 今天就是演出日！",
        header_subtitle="好好享受今天的演出 ✨",
        body_contents=body_contents,
        alt_text="🎤 演出日提醒",
    )