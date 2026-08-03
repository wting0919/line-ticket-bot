from datetime import datetime, timedelta

from linebot.models import FlexSendMessage

import config

from show_list import (
    get_all_shows,
)

from today_card import (
    get_today_ticket_shows,
    get_today_pickup_shows,
    get_today_show_shows,
)

from utils import (
    parse_date,
    format_show_dates_inline,
)


# =========================================================
# Dashboard V1
# 奶茶色系
# =========================================================

HEADER_COLOR = "#C9B29B"
BODY_COLOR = "#FFFCF8"

CARD_COLOR = "#FFFFFF"
SECTION_COLOR = "#F4ECE4"

TICKET_CARD_COLOR = "#FFF4D6"
PICKUP_CARD_COLOR = "#EEF3E8"
SHOW_CARD_COLOR = "#F8EAE4"

TEXT_COLOR = "#5C5148"
SUBTEXT_COLOR = "#75695F"
LIGHT_TEXT_COLOR = "#9A8D82"

LINE_COLOR = "#E7DDD2"
BUTTON_COLOR = "#B99F86"

WHITE_COLOR = "#FFFFFF"
HEADER_SUBTEXT_COLOR = "#FFF9F3"

FOOTER_COLOR = "#F4E4D4"


# =========================================================
# 基本工具
# =========================================================

def safe_text(
    value,
    default="未設定",
):
    """
    安全處理空值。
    """

    if value is None:
        return default

    text = str(value).strip()

    return text if text else default


def remove_none_elements(value):
    """
    遞迴移除 Flex JSON 中的 None，
    避免 LINE 回傳 null element 錯誤。
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


def normalize_today(today=None):
    """
    統一取得台灣時間。
    """

    if today is None:
        return datetime.now() + timedelta(hours=8)

    if isinstance(today, datetime):
        return today

    return datetime.combine(
        today,
        datetime.min.time(),
    )


def build_separator(
    margin="lg",
):
    """
    建立奶茶色分隔線。
    """

    return {
        "type": "separator",
        "margin": margin,
        "color": LINE_COLOR,
    }


# =========================================================
# Logo
# =========================================================

def get_dashboard_logo_url():
    """
    從 config 讀取 Logo 公開網址。

    沒有設定時，Header 會自動省略圖片，
    不影響 Dashboard 顯示。
    """

    logo_url = getattr(
        config,
        "DASHBOARD_LOGO_URL",
        None,
    )

    if not logo_url:
        return None

    logo_url = str(logo_url).strip()

    if not logo_url.startswith("https://"):
        return None

    return logo_url


def build_logo():
    """
    建立圓形搶票貓 Logo。
    """

    logo_url = get_dashboard_logo_url()

    if not logo_url:
        return None

    return {
        "type": "image",
        "url": logo_url,
        "size": "full",
        "aspectMode": "cover",
        "aspectRatio": "1:1",
    }


def build_logo_box():
    """
    Logo 外框。
    """

    logo = build_logo()

    if logo is None:

        return {
            "type": "box",
            "layout": "vertical",
            "width": "66px",
            "height": "66px",
            "backgroundColor": "#FFF7EC",
            "cornerRadius": "33px",
            "justifyContent": "center",
            "alignItems": "center",
            "contents": [
                {
                    "type": "text",
                    "text": "🐱",
                    "size": "xxl",
                    "align": "center",
                }
            ],
        }

    return {
        "type": "box",
        "layout": "vertical",
        "width": "66px",
        "height": "66px",
        "cornerRadius": "33px",
        "contents": [
            logo
        ],
    }


# =========================================================
# Header
# =========================================================

def build_header():
    """
    建立 Dashboard Header。
    """

    return {
        "type": "box",
        "layout": "vertical",
        "backgroundColor": HEADER_COLOR,
        "paddingTop": "18px",
        "paddingBottom": "18px",
        "paddingStart": "18px",
        "paddingEnd": "18px",
        "contents": [
            {
                "type": "box",
                "layout": "horizontal",
                "alignItems": "center",
                "contents": [
                    build_logo_box(),
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "md",
                        "flex": 1,
                        "contents": [
                            {
                                "type": "text",
                                "text": "演唱會小助手",
                                "size": "xl",
                                "weight": "bold",
                                "color": WHITE_COLOR,
                                "wrap": True,
                            },
                            {
                                "type": "text",
                                "text": "所有重要行程，一目了然",
                                "size": "xs",
                                "color": HEADER_SUBTEXT_COLOR,
                                "margin": "sm",
                                "wrap": True,
                            },
                        ],
                    },
                ],
            },
            {
                "type": "box",
                "layout": "vertical",
                "margin": "md",
                "backgroundColor": "#FFF7EC",
                "cornerRadius": "14px",
                "paddingTop": "8px",
                "paddingBottom": "8px",
                "paddingStart": "12px",
                "paddingEnd": "12px",
                "contents": [
                    {
                        "type": "text",
                        "text": "🐾 今天也加油搶票！",
                        "size": "xs",
                        "weight": "bold",
                        "color": TEXT_COLOR,
                        "align": "center",
                        "wrap": True,
                    }
                ],
            },
        ],
    }


# =========================================================
# 今日待辦摘要
# =========================================================

def build_summary_card(
    icon,
    label,
    count,
    background_color,
    action_text,
):
    """
    建立可點擊的單格摘要。
    """

    return {
        "type": "box",
        "layout": "vertical",
        "flex": 1,
        "backgroundColor": background_color,
        "cornerRadius": "14px",
        "paddingTop": "13px",
        "paddingBottom": "13px",
        "paddingStart": "5px",
        "paddingEnd": "5px",
        "action": {
            "type": "message",
            "label": label,
            "text": action_text,
        },
        "contents": [
            {
                "type": "text",
                "text": icon,
                "size": "xl",
                "align": "center",
            },
            {
                "type": "text",
                "text": label,
                "size": "xxs",
                "weight": "bold",
                "color": SUBTEXT_COLOR,
                "align": "center",
                "margin": "sm",
                "wrap": False,
            },
            {
                "type": "text",
                "text": str(count),
                "size": "xxl",
                "weight": "bold",
                "color": TEXT_COLOR,
                "align": "center",
                "margin": "xs",
            },
            {
                "type": "text",
                "text": "項",
                "size": "xxs",
                "color": LIGHT_TEXT_COLOR,
                "align": "center",
            },
        ],
    }


def build_today_summary(
    ticket_count,
    pickup_count,
    show_count,
):
    """
    建立今日待辦摘要。
    """

    total_count = (
        ticket_count
        + pickup_count
        + show_count
    )

    return {
        "type": "box",
        "layout": "vertical",
        "backgroundColor": CARD_COLOR,
        "cornerRadius": "16px",
        "paddingAll": "14px",
        "borderWidth": "1px",
        "borderColor": LINE_COLOR,
        "contents": [
            {
                "type": "box",
                "layout": "horizontal",
                "alignItems": "center",
                "action": {
                    "type": "message",
                    "label": "今日待辦",
                    "text": "今日待辦",
                },
                "contents": [
                    {
                        "type": "text",
                        "text": "☀️ 今日待辦",
                        "size": "lg",
                        "weight": "bold",
                        "color": TEXT_COLOR,
                        "flex": 1,
                        "wrap": True,
                    },
                    {
                        "type": "text",
                        "text": f"共 {total_count} 項",
                        "size": "xs",
                        "color": SUBTEXT_COLOR,
                        "align": "end",
                        "wrap": False,
                    },
                ],
            },
            {
                "type": "box",
                "layout": "horizontal",
                "spacing": "sm",
                "margin": "lg",
                "contents": [
                    build_summary_card(
                        icon="🎟",
                        label="待搶票",
                        count=ticket_count,
                        background_color=TICKET_CARD_COLOR,
                        action_text="搶票列表",
                    ),
                    build_summary_card(
                        icon="📦",
                        label="待取票",
                        count=pickup_count,
                        background_color=PICKUP_CARD_COLOR,
                        action_text="取票列表",
                    ),
                    build_summary_card(
                        icon="🎤",
                        label="今日演出",
                        count=show_count,
                        background_color=SHOW_CARD_COLOR,
                        action_text="今日待辦",
                    ),
                ],
            },
        ],
    }


# =========================================================
# 下一場演出
# =========================================================

def split_show_dates(show_dates):
    """
    將演出日期整理成日期列表。
    """

    if not show_dates:
        return []

    if isinstance(
        show_dates,
        (list, tuple),
    ):

        return [
            str(value).strip()
            for value in show_dates
            if str(value).strip()
        ]

    text = (
        str(show_dates)
        .replace("，", ",")
        .replace("\n", ",")
    )

    return [
        value.strip()
        for value in text.split(",")
        if value.strip()
    ]


def get_first_future_show_date(
    show,
    today,
):
    """
    取得一筆演出最早且尚未過期的日期。
    """

    parsed_dates = []

    for date_value in split_show_dates(
        show.get("演出日期")
    ):

        parsed_date = parse_date(
            date_value
        )

        if parsed_date is None:
            continue

        if hasattr(parsed_date, "date"):
            date_result = parsed_date.date()
        else:
            date_result = parsed_date

        if date_result >= today.date():
            parsed_dates.append(date_result)

    if not parsed_dates:
        return None

    return min(parsed_dates)


def get_next_show(
    shows,
    today,
):
    """
    取得下一場演出。
    """

    candidates = []

    for show in shows or []:

        show_date = get_first_future_show_date(
            show,
            today,
        )

        if show_date is None:
            continue

        candidates.append(
            (
                show_date,
                show,
            )
        )

    if not candidates:
        return None, None

    candidates.sort(
        key=lambda item: item[0]
    )

    return candidates[0]


def build_next_show_card(
    show,
    show_date,
    today,
):
    """
    建立下一場演出卡。
    """

    if show is None or show_date is None:

        return {
            "type": "box",
            "layout": "vertical",
            "margin": "lg",
            "backgroundColor": SECTION_COLOR,
            "cornerRadius": "14px",
            "paddingAll": "16px",
            "contents": [
                {
                    "type": "text",
                    "text": "🐱 尚未有即將到來的演出",
                    "size": "sm",
                    "weight": "bold",
                    "color": TEXT_COLOR,
                    "align": "center",
                    "wrap": True,
                },
                {
                    "type": "text",
                    "text": "新增一場演出，讓搶票貓幫你記住吧！",
                    "size": "xs",
                    "color": SUBTEXT_COLOR,
                    "align": "center",
                    "margin": "sm",
                    "wrap": True,
                },
            ],
        }

    days_left = (
        show_date - today.date()
    ).days

    if days_left == 0:
        countdown_text = "就是今天"
    elif days_left == 1:
        countdown_text = "還有 1 天"
    else:
        countdown_text = f"還有 {days_left} 天"

    show_id = safe_text(
        show.get("id"),
        "",
    )

    if show_id:
        action_text = f"查看ID {show_id}"
    else:
        action_text = "演出列表"

    return {
        "type": "box",
        "layout": "vertical",
        "margin": "lg",
        "backgroundColor": SECTION_COLOR,
        "cornerRadius": "14px",
        "paddingAll": "15px",
        "action": {
            "type": "message",
            "label": "查看下一場演出",
            "text": action_text,
        },
        "contents": [
            {
                "type": "text",
                "text": "📅 下一場演出",
                "size": "xs",
                "weight": "bold",
                "color": SUBTEXT_COLOR,
            },
            {
                "type": "text",
                "text": (
                    f"🎤 "
                    f"{safe_text(show.get('演出名稱'), '未命名演出')}"
                ),
                "size": "lg",
                "weight": "bold",
                "color": TEXT_COLOR,
                "margin": "md",
                "wrap": True,
            },
            {
                "type": "text",
                "text": format_show_dates_inline(
                    show.get("演出日期")
                ),
                "size": "sm",
                "color": SUBTEXT_COLOR,
                "margin": "sm",
                "wrap": True,
            },
            {
                "type": "box",
                "layout": "horizontal",
                "margin": "md",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "backgroundColor": TICKET_CARD_COLOR,
                        "cornerRadius": "12px",
                        "paddingTop": "6px",
                        "paddingBottom": "6px",
                        "paddingStart": "12px",
                        "paddingEnd": "12px",
                        "contents": [
                            {
                                "type": "text",
                                "text": countdown_text,
                                "size": "xs",
                                "weight": "bold",
                                "color": TEXT_COLOR,
                                "align": "center",
                            }
                        ],
                    },
                    {
                        "type": "text",
                        "text": "›",
                        "size": "xl",
                        "weight": "bold",
                        "color": BUTTON_COLOR,
                        "align": "end",
                        "flex": 1,
                    },
                ],
            },
        ],
    }


# =========================================================
# 功能選單
# =========================================================

def build_menu_item(
    icon,
    title,
    description,
    action_text,
    icon_background=SECTION_COLOR,
):
    """
    建立單一功能入口。
    """

    return {
        "type": "box",
        "layout": "horizontal",
        "backgroundColor": CARD_COLOR,
        "cornerRadius": "13px",
        "paddingTop": "12px",
        "paddingBottom": "12px",
        "paddingStart": "12px",
        "paddingEnd": "12px",
        "borderWidth": "1px",
        "borderColor": LINE_COLOR,
        "alignItems": "center",
        "action": {
            "type": "message",
            "label": title,
            "text": action_text,
        },
        "contents": [
            {
                "type": "box",
                "layout": "vertical",
                "width": "42px",
                "height": "42px",
                "backgroundColor": icon_background,
                "cornerRadius": "21px",
                "justifyContent": "center",
                "alignItems": "center",
                "contents": [
                    {
                        "type": "text",
                        "text": icon,
                        "size": "lg",
                        "align": "center",
                    }
                ],
            },
            {
                "type": "box",
                "layout": "vertical",
                "margin": "md",
                "flex": 1,
                "contents": [
                    {
                        "type": "text",
                        "text": title,
                        "size": "sm",
                        "weight": "bold",
                        "color": TEXT_COLOR,
                        "wrap": True,
                    },
                    {
                        "type": "text",
                        "text": description,
                        "size": "xxs",
                        "color": SUBTEXT_COLOR,
                        "margin": "xs",
                        "wrap": True,
                    },
                ],
            },
            {
                "type": "text",
                "text": "›",
                "size": "xl",
                "weight": "bold",
                "color": BUTTON_COLOR,
                "align": "end",
                "flex": 0,
            },
        ],
    }


def build_menu_area():
    """
    建立首頁功能選單。
    """

    return {
        "type": "box",
        "layout": "vertical",
        "spacing": "sm",
        "margin": "lg",
        "contents": [
            build_menu_item(
                icon="📋",
                title="演出列表",
                description="查看所有演出資料",
                action_text="演出列表",
                icon_background="#F4E6D7",
            ),
            build_menu_item(
                icon="🎟",
                title="搶票列表",
                description="查看即將開始搶票的演出",
                action_text="搶票列表",
                icon_background=TICKET_CARD_COLOR,
            ),
            build_menu_item(
                icon="📦",
                title="取票列表",
                description="查看尚未取票的演出",
                action_text="取票列表",
                icon_background=PICKUP_CARD_COLOR,
            ),
            build_menu_item(
                icon="➕",
                title="新增演出",
                description="新增一筆演出到小助手",
                action_text="新增演出",
                icon_background="#F2DDC9",
            ),
            build_menu_item(
                icon="❓",
                title="使用說明",
                description="查看指令說明與使用方式",
                action_text="幫助",
                icon_background="#EEE1D5",
            ),
        ],
    }


# =========================================================
# Footer
# =========================================================

def build_footer(
    total_show_count,
    total_task_count,
):
    """
    建立 Dashboard Footer。
    """

    if total_show_count == 0:

        title = "🐱 尚未新增任何演出"
        subtitle = "新增第一場演出，讓搶票貓開始工作吧！"

    elif total_task_count == 0:

        title = f"🐱 目前共有 {total_show_count} 場演出"
        subtitle = "今天沒有待辦，好好休息一下～"

    else:

        title = f"🐱 今天共有 {total_task_count} 項待辦"
        subtitle = f"目前共管理 {total_show_count} 場演出"

    return {
        "type": "box",
        "layout": "horizontal",
        "margin": "lg",
        "backgroundColor": FOOTER_COLOR,
        "cornerRadius": "14px",
        "paddingTop": "12px",
        "paddingBottom": "12px",
        "paddingStart": "14px",
        "paddingEnd": "14px",
        "alignItems": "center",
        "contents": [
            {
                "type": "text",
                "text": "📣",
                "size": "lg",
                "flex": 0,
            },
            {
                "type": "box",
                "layout": "vertical",
                "margin": "md",
                "flex": 1,
                "contents": [
                    {
                        "type": "text",
                        "text": title,
                        "size": "sm",
                        "weight": "bold",
                        "color": TEXT_COLOR,
                        "wrap": True,
                    },
                    {
                        "type": "text",
                        "text": subtitle,
                        "size": "xxs",
                        "color": SUBTEXT_COLOR,
                        "margin": "xs",
                        "wrap": True,
                    },
                ],
            },
        ],
    }


# =========================================================
# 建立 Dashboard
# =========================================================

def build_dashboard(today=None):
    """
    建立完整首頁 Dashboard。
    """

    today = normalize_today(today)

    all_shows = (
        get_all_shows()
        or []
    )

    ticket_shows = (
        get_today_ticket_shows(today)
        or []
    )

    pickup_shows = (
        get_today_pickup_shows(today)
        or []
    )

    show_shows = (
        get_today_show_shows(today)
        or []
    )

    ticket_count = len(ticket_shows)
    pickup_count = len(pickup_shows)
    show_count = len(show_shows)

    total_task_count = (
        ticket_count
        + pickup_count
        + show_count
    )

    next_show_date, next_show = get_next_show(
        all_shows,
        today,
    )

    body_contents = [
        build_today_summary(
            ticket_count=ticket_count,
            pickup_count=pickup_count,
            show_count=show_count,
        ),
        build_next_show_card(
            show=next_show,
            show_date=next_show_date,
            today=today,
        ),
        build_menu_area(),
        build_footer(
            total_show_count=len(all_shows),
            total_task_count=total_task_count,
        ),
    ]

    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": build_header(),
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": BODY_COLOR,
            "paddingTop": "16px",
            "paddingBottom": "16px",
            "paddingStart": "14px",
            "paddingEnd": "14px",
            "contents": body_contents,
        },
        "styles": {
            "header": {
                "separator": False,
            },
            "body": {
                "separator": False,
            },
        },
    }

    bubble = remove_none_elements(
        bubble
    )

    return FlexSendMessage(
        alt_text="🐱 演唱會小助手",
        contents=bubble,
    )


# =========================================================
# 相容名稱
# =========================================================

def create_dashboard(today=None):
    return build_dashboard(today)


def get_dashboard(today=None):
    return build_dashboard(today)