import config
import random

from datetime import datetime, timedelta

from linebot.models import FlexSendMessage

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

from components import (
    build_today_summary,
)

from theme import (
    BODY_COLOR,
    CARD_COLOR,
    SECTION_COLOR,
    TICKET_CARD_COLOR,
    TEXT_COLOR,
    SUBTEXT_COLOR,
    LIGHT_TEXT_COLOR,
    LINE_COLOR,
    BUTTON_COLOR,
    build_brand_header,
    build_brand_footer,
    safe_text,
    remove_none_elements,
)

# =========================================================
# TicketCat 每日一句
# =========================================================

CAT_HEADER_MESSAGES = [
    "🐾 今天也加油搶票！",
    "🐾 希望今天是神手的一天！",
    "🐾 搶票模式 ON！",
    "🐾 祝你今天歐氣滿滿 🍀",
    "🐾 今天一定有好消息！",
]


def get_cat_header_message():
    """
    每天固定顯示一句 TicketCat 訊息。

    使用日期作為亂數種子，
    同一天內每次開啟 Dashboard 都會顯示同一句。
    """

    taiwan_now = datetime.now() + timedelta(hours=8)

    date_seed = taiwan_now.strftime(
        "%Y%m%d"
    )

    random_generator = random.Random(
        date_seed
    )

    return random_generator.choice(
        CAT_HEADER_MESSAGES
    )


# =========================================================
# 基本工具
# =========================================================

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

# =========================================================
# Header
# =========================================================

def build_header():
    """
    建立 Dashboard 品牌 Header。
    """

    return build_brand_header(
        subtitle=None,
        message=get_cat_header_message(),
        logo_size=44,
        compact=True,
    )

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
                    "text": "新增一場演出，讓 TicketCat 幫你記住吧！",
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
        "margin": "md",
        "backgroundColor": SECTION_COLOR,
        "cornerRadius": "14px",
        "paddingTop": "11px",
        "paddingBottom": "11px",
        "paddingStart": "12px",
        "paddingEnd": "12px",
        "action": {
            "type": "message",
            "label": "查看下一場演出",
            "text": action_text,
        },
        "contents": [
            {
                "type": "box",
                "layout": "horizontal",
                "alignItems": "center",
                "contents": [
                    {
                        "type": "text",
                        "text": "📅 下一場演出",
                        "size": "xs",
                        "weight": "bold",
                        "color": SUBTEXT_COLOR,
                        "flex": 1,
                        "wrap": False,
                    },
                    {
                        "type": "text",
                        "text": format_show_dates_inline(
                            show.get("演出日期")
                        ),
                        "size": "xxs",
                        "color": SUBTEXT_COLOR,
                        "align": "end",
                        "flex": 0,
                        "wrap": True,
                    },
                ],
            },
            {
                "type": "text",
                "text": (
                    f"🎤 "
                    f"{safe_text(show.get('演出名稱'), '未命名演出')}"
                ),
                "size": "sm",
                "weight": "bold",
                "color": TEXT_COLOR,
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
                        "paddingTop": "5px",
                        "paddingBottom": "5px",
                        "paddingStart": "14px",
                        "paddingEnd": "14px",
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
        "paddingTop": "10px",
        "paddingBottom": "10px",
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
                "width": "38px",
                "height": "38px",
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
                description="新增一筆演出資料",
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
        build_brand_footer(),
    ]

    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": build_header(),
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": BODY_COLOR,
            "paddingTop": "12px",
            "paddingBottom": "12px",
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
        alt_text="🐱 TicketCat",
        contents=bubble,
    )


# =========================================================
# 相容名稱
# =========================================================

def create_dashboard(today=None):
    return build_dashboard(today)


def get_dashboard(today=None):
    return build_dashboard(today)