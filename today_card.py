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


# =========================================================
# Today Card V3
# 奶茶色系
# =========================================================

HEADER_COLOR = "#C9B29B"
BODY_COLOR = "#FFFCF8"
SECTION_COLOR = "#F4ECE4"
EMPTY_COLOR = "#FAF5EF"

TEXT_COLOR = "#5C5148"
SUBTEXT_COLOR = "#75695F"
LIGHT_TEXT_COLOR = "#9A8D82"

LINE_COLOR = "#E7DDD2"

BUTTON_COLOR = "#B99F86"

TAG_COLOR = "#F1E8DE"
TAG_TEXT_COLOR = "#75695F"

WHITE_COLOR = "#FFFFFF"
HEADER_SUBTEXT_COLOR = "#FFF9F3"


# =========================================================
# 基本工具
# =========================================================

def safe_text(value, default="未設定"):
    """
    安全處理文字欄位。

    None、空字串或純空白時，
    回傳預設文字。
    """

    if value is None:
        return default

    text = str(value).strip()

    if not text:
        return default

    return text


def get_show_detail_action(
    show,
    fallback_text="演出列表",
):
    """
    有 Supabase id 時直接查看該筆詳細；
    沒有 id 時回到指定列表。
    """

    show_id = str(
        show.get("id") or ""
    ).strip()

    if show_id:
        return f"查看ID {show_id}"

    return fallback_text


def normalize_today(today=None):
    """
    將 today 統一轉成 datetime。

    支援：
    - None
    - datetime
    - datetime.date
    """

    if today is None:
        return datetime.now()

    if isinstance(today, datetime):
        return today

    return datetime.combine(
        today,
        datetime.min.time(),
    )


# =========================================================
# 共用 Flex 元件
# =========================================================

def build_text(
    text,
    size="sm",
    color=TEXT_COLOR,
    weight="regular",
    wrap=True,
    flex=None,
    align=None,
    margin=None,
):
    """
    建立共用文字元件。
    """

    component = {
        "type": "text",
        "text": safe_text(text, ""),
        "size": size,
        "color": color,
        "weight": weight,
        "wrap": wrap,
    }

    if flex is not None:
        component["flex"] = flex

    if align is not None:
        component["align"] = align

    if margin is not None:
        component["margin"] = margin

    return component


def build_separator(margin="md"):
    """
    建立奶茶色分隔線。
    """

    return {
        "type": "separator",
        "margin": margin,
        "color": LINE_COLOR,
    }


def build_status_tag(
    text,
    color=TAG_COLOR,
    text_color=TAG_TEXT_COLOR,
):
    """
    建立狀態標籤。
    """

    return {
        "type": "box",
        "layout": "vertical",
        "backgroundColor": color,
        "cornerRadius": "10px",
        "paddingTop": "3px",
        "paddingBottom": "3px",
        "paddingStart": "8px",
        "paddingEnd": "8px",
        "contents": [
            {
                "type": "text",
                "text": safe_text(text, ""),
                "size": "xxs",
                "color": text_color,
                "weight": "bold",
                "align": "center",
                "wrap": False,
            }
        ],
    }


def build_info_row(label, value):
    """
    建立單筆欄位資訊。

    範例：
    搶票時間　2026/08/02 12:00
    """

    return {
        "type": "box",
        "layout": "horizontal",
        "margin": "xs",
        "contents": [
            {
                "type": "text",
                "text": safe_text(label, ""),
                "size": "xs",
                "color": SUBTEXT_COLOR,
                "weight": "bold",
                "wrap": True,
                "flex": 3,
            },
            {
                "type": "text",
                "text": safe_text(value),
                "size": "xs",
                "color": TEXT_COLOR,
                "wrap": True,
                "flex": 7,
            },
        ],
    }


def build_task_item(
    title,
    info_rows=None,
    badge_text=None,
    action_text=None,
):
    """
    建立單筆今日待辦項目。

    整個項目可以直接點擊，
    進入該筆演出詳細資料。
    """

    info_rows = info_rows or []

    title_contents = [
        {
            "type": "text",
            "text": safe_text(
                title,
                "未命名演出",
            ),
            "size": "md",
            "weight": "bold",
            "color": TEXT_COLOR,
            "wrap": True,
            "flex": 1,
        }
    ]

    if badge_text:

        title_contents.append(
            {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": TAG_COLOR,
                "cornerRadius": "10px",
                "paddingTop": "3px",
                "paddingBottom": "3px",
                "paddingStart": "8px",
                "paddingEnd": "8px",
                "margin": "sm",
                "contents": [
                    {
                        "type": "text",
                        "text": safe_text(
                            badge_text,
                            "",
                        ),
                        "size": "xxs",
                        "weight": "bold",
                        "color": TAG_TEXT_COLOR,
                        "align": "center",
                        "wrap": False,
                    }
                ],
            }
        )

    contents = [
        {
            "type": "box",
            "layout": "horizontal",
            "alignItems": "center",
            "contents": title_contents,
        }
    ]

    for label, value in info_rows:

        contents.append(
            build_info_row(
                label,
                value,
            )
        )

    item = {
        "type": "box",
        "layout": "vertical",
        "spacing": "sm",
        "paddingTop": "4px",
        "paddingBottom": "4px",
        "contents": contents,
    }

    if action_text:

        item["action"] = {
            "type": "message",
            "label": "查看詳細",
            "text": action_text,
        }

    return item

# =========================================================
# 日期顯示
# =========================================================

def get_weekday_text(date_value):
    """
    將星期轉成中文。
    """

    weekdays = [
        "星期一",
        "星期二",
        "星期三",
        "星期四",
        "星期五",
        "星期六",
        "星期日",
    ]

    return weekdays[
        date_value.weekday()
    ]


def format_today_date(date_value):
    """
    將日期格式化為：

    2026年8月2日 星期日
    """

    weekday = get_weekday_text(
        date_value
    )

    return (
        f"{date_value.year}年"
        f"{date_value.month}月"
        f"{date_value.day}日 "
        f"{weekday}"
    )


# =========================================================
# Header
# =========================================================

def build_header(today):
    """
    建立「☀️ 今日待辦事項」標題。
    """

    return {
        "type": "box",
        "layout": "vertical",
        "backgroundColor": HEADER_COLOR,
        "paddingTop": "14px",
        "paddingBottom": "14px",
        "paddingStart": "16px",
        "paddingEnd": "16px",
        "contents": [
            {
                "type": "text",
                "text": "☀️ 今日待辦事項",
                "size": "lg",
                "weight": "bold",
                "color": WHITE_COLOR,
                "wrap": True,
            },
            {
                "type": "text",
                "text": format_today_date(
                    today,
                ),
                "size": "xs",
                "color": HEADER_SUBTEXT_COLOR,
                "margin": "sm",
                "wrap": True,
            },
        ],
    }


# =========================================================
# Section 標題
# =========================================================

def build_section_title(
    icon,
    title,
    count=None,
):
    """
    建立區塊標題。

    範例：
    🎟 今日搶票    2
    """

    contents = [
        {
            "type": "text",
            "text": (
                f"{safe_text(icon, '')} "
                f"{safe_text(title, '')}"
            ),
            "size": "md",
            "weight": "bold",
            "color": TEXT_COLOR,
            "wrap": True,
            "flex": 1,
        }
    ]

    if count is not None:
        contents.append(
            build_status_tag(
                text=str(count),
            )
        )

    return {
        "type": "box",
        "layout": "horizontal",
        "alignItems": "center",
        "contents": contents,
    }


# =========================================================
# 空白狀態
# =========================================================

def build_empty_content(empty_text):
    """
    建立區塊沒有資料時的顯示內容。
    """

    return {
        "type": "box",
        "layout": "vertical",
        "backgroundColor": EMPTY_COLOR,
        "cornerRadius": "10px",
        "paddingAll": "12px",
        "contents": [
            {
                "type": "text",
                "text": safe_text(
                    empty_text,
                    "目前沒有待辦事項",
                ),
                "size": "sm",
                "color": LIGHT_TEXT_COLOR,
                "align": "center",
                "wrap": True,
            }
        ],
    }


# =========================================================
# 共用 Section
# =========================================================

def build_section(
    icon,
    title,
    items,
    item_builder,
    empty_text="目前沒有待辦事項",
    show_count=True,
    margin="lg",
):
    """
    建立共用待辦區塊。
    """

    safe_items = items or []

    section_contents = [
        build_section_title(
            icon=icon,
            title=title,
            count=(
                len(safe_items)
                if show_count
                else None
            ),
        ),
        build_separator(
            margin="md",
        ),
    ]

    if not safe_items:
        section_contents.append(
            {
                "type": "box",
                "layout": "vertical",
                "margin": "md",
                "contents": [
                    build_empty_content(
                        empty_text,
                    )
                ],
            }
        )

    else:
        item_contents = []

        for index, item in enumerate(
            safe_items,
            start=1,
        ):
            try:
                built_item = item_builder(
                    item,
                    index,
                )

            except TypeError:
                built_item = item_builder(
                    item
                )

            except Exception as error:
                print(
                    "[today_card] "
                    "建立區塊項目失敗："
                    f"title={title}, "
                    f"index={index}, "
                    f"error={repr(error)}",
                    flush=True,
                )

                continue

            if not built_item:
                continue

            if item_contents:
                item_contents.append(
                    build_separator(
                        margin="md",
                    )
                )

            item_contents.append(
                built_item
            )

        if item_contents:
            section_contents.append(
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "md",
                    "spacing": "md",
                    "contents": item_contents,
                }
            )

        else:
            section_contents.append(
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "md",
                    "contents": [
                        build_empty_content(
                            empty_text,
                        )
                    ],
                }
            )

    return {
        "type": "box",
        "layout": "vertical",
        "margin": margin,
        "contents": section_contents,
    }

# =========================================================
# 日期判斷工具
# =========================================================

def is_same_date(
    value,
    target_date,
):
    """
    判斷日期或日期時間是否為指定日期。
    """

    if not value:
        return False

    parsed_value = parse_datetime(
        value
    )

    if parsed_value is None:
        parsed_value = parse_date(
            value
        )

    if parsed_value is None:
        return False

    return (
        parsed_value.date()
        == target_date.date()
    )


def split_show_dates(show_dates):
    """
    將演出日期統一整理成日期字串列表。

    支援：
    - 單一日期
    - list / tuple
    - 中文逗號
    - 英文逗號
    - 換行
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

    text = str(show_dates).strip()

    text = text.replace(
        "，",
        ",",
    )

    text = text.replace(
        "\n",
        ",",
    )

    return [
        value.strip()
        for value in text.split(",")
        if value.strip()
    ]


def is_show_date_today(
    show,
    today,
):
    """
    判斷演出是否在今天。
    """

    date_values = split_show_dates(
        show.get("演出日期")
    )

    return any(
        is_same_date(
            value,
            today,
        )
        for value in date_values
    )


# =========================================================
# 今日資料篩選
# =========================================================

def get_today_ticket_shows(today):
    """
    取得今天需要搶票的演出。
    """

    waiting_shows = (
        get_waiting_shows()
        or []
    )

    return [
        show
        for show in waiting_shows
        if is_same_date(
            show.get("搶票時間"),
            today,
        )
    ]


def get_today_pickup_shows(today):
    """
    取得今天需要取票的演出。
    """

    pickup_shows = (
        get_pickup_shows()
        or []
    )

    return [
        show
        for show in pickup_shows
        if is_same_date(
            show.get("取票日期"),
            today,
        )
    ]


def get_today_show_shows(today):
    """
    取得今天舉行的演出。
    """

    all_shows = (
        get_all_shows()
        or []
    )

    return [
        show
        for show in all_shows
        if is_show_date_today(
            show,
            today,
        )
    ]


# =========================================================
# 排序工具
# =========================================================

def sort_today_ticket_shows(shows):
    """
    今日搶票依搶票時間排序。
    """

    return sorted(
        shows or [],
        key=lambda show: (
            parse_datetime(
                show.get("搶票時間")
            )
            or datetime.max
        ),
    )


def sort_today_pickup_shows(shows):
    """
    今日取票依取票日期排序。
    """

    return sorted(
        shows or [],
        key=lambda show: (
            parse_date(
                show.get("取票日期")
            )
            or datetime.max
        ),
    )


def get_first_show_date(show):
    """
    取得演出的第一個日期，
    供今日演出排序使用。
    """

    date_values = split_show_dates(
        show.get("演出日期")
    )

    parsed_dates = []

    for value in date_values:
        parsed_date = parse_date(
            value
        )

        if parsed_date is not None:
            parsed_dates.append(
                parsed_date
            )

    if not parsed_dates:
        return datetime.max

    return min(
        parsed_dates
    )


def sort_today_show_shows(shows):
    """
    今日演出依演出日期排序。
    """

    return sorted(
        shows or [],
        key=get_first_show_date,
    )


# =========================================================
# 今日搶票項目
# =========================================================

def build_ticket_item(
    show,
    index,
):
    """
    建立今日搶票項目。
    """

    ticket_time = format_datetime(
        show.get("搶票時間")
    )

    platform = safe_text(
        show.get("售票平台")
    )

    price_quantity = safe_text(
        show.get("價格張數")
    )

    note = show.get("備註")

    info_rows = [
        (
            "搶票時間",
            ticket_time,
        ),
        (
            "售票平台",
            platform,
        ),
        (
            "價格張數",
            price_quantity,
        ),
    ]

    if note:
        info_rows.append(
            (
                "備註",
                note,
            )
        )

    return build_task_item(
        title=show.get("演出名稱"),
        info_rows=info_rows,
        badge_text="待搶票",
        action_text=get_show_detail_action(
            show,
            fallback_text="搶票列表",
        ),
    )


# =========================================================
# 今日取票項目
# =========================================================

def build_pickup_item(
    show,
    index,
):
    """
    建立今日取票項目。
    """

    pickup_date = parse_date(
        show.get("取票日期")
    )

    if pickup_date:
        pickup_date_text = (
            pickup_date.strftime(
                "%Y / %m / %d"
            )
        )

    else:
        pickup_date_text = safe_text(
            show.get("取票日期")
        )

    show_dates = (
        format_show_dates_inline(
            show.get("演出日期")
        )
    )

    platform = show.get(
        "售票平台"
    )

    info_rows = [
        (
            "取票日期",
            pickup_date_text,
        ),
        (
            "演出日期",
            show_dates,
        ),
    ]

    if platform:
        info_rows.append(
            (
                "售票平台",
                platform,
            )
        )

    return build_task_item(
        title=show.get("演出名稱"),
        info_rows=info_rows,
        badge_text="未取票",
        action_text=get_show_detail_action(
            show,
            fallback_text="取票列表",
        ),
    )


# =========================================================
# 今日演出項目
# =========================================================

def build_show_item(
    show,
    index,
):
    """
    建立今日演出項目。
    """

    show_dates = (
        format_show_dates_inline(
            show.get("演出日期")
        )
    )

    platform = show.get(
        "售票平台"
    )

    note = show.get(
        "備註"
    )

    info_rows = [
        (
            "演出日期",
            show_dates,
        ),
    ]

    if platform:
        info_rows.append(
            (
                "售票平台",
                platform,
            )
        )

    if note:
        info_rows.append(
            (
                "備註",
                note,
            )
        )

    return build_task_item(
        title=show.get("演出名稱"),
        info_rows=info_rows,
        badge_text="演出日",
        action_text=get_show_detail_action(
            show,
            fallback_text="演出列表",
        ),
    )


# =========================================================
# 統計摘要
# =========================================================

def build_summary_count(
    icon,
    label,
    count,
    action_text,
):
    """
    建立摘要中的單一統計欄位。

    點擊後送出對應列表指令。
    """

    return {
        "type": "box",
        "layout": "vertical",
        "flex": 1,
        "paddingAll": "8px",
        "backgroundColor": SECTION_COLOR,
        "cornerRadius": "10px",
        "action": {
            "type": "message",
            "label": f"查看{label}列表",
            "text": action_text,
        },
        "contents": [
            {
                "type": "text",
                "text": icon,
                "size": "md",
                "align": "center",
            },
            {
                "type": "text",
                "text": str(count),
                "size": "lg",
                "weight": "bold",
                "color": TEXT_COLOR,
                "align": "center",
                "margin": "xs",
            },
            {
                "type": "text",
                "text": label,
                "size": "xxs",
                "color": SUBTEXT_COLOR,
                "align": "center",
                "margin": "xs",
            },
        ],
    }


def build_summary(
    ticket_count,
    pickup_count,
    show_count,
):
    """
    建立今日待辦數量摘要。

    三個統計區塊可直接點擊。
    """

    total_count = (
        ticket_count
        + pickup_count
        + show_count
    )

    summary_text = (
        f"今天共有 {total_count} 項待辦"
    )

    return {
        "type": "box",
        "layout": "vertical",
        "paddingAll": "14px",
        "backgroundColor": BODY_COLOR,
        "cornerRadius": "12px",
        "borderWidth": "1px",
        "borderColor": LINE_COLOR,
        "contents": [
            {
                "type": "text",
                "text": summary_text,
                "size": "sm",
                "weight": "bold",
                "color": TEXT_COLOR,
                "align": "center",
                "wrap": True,
            },
            {
                "type": "box",
                "layout": "horizontal",
                "margin": "md",
                "spacing": "sm",
                "contents": [
                    build_summary_count(
                        icon="🎟",
                        label="待搶票",
                        count=ticket_count,
                        action_text="搶票列表",
                    ),
                    build_summary_count(
                        icon="📦",
                        label="待取票",
                        count=pickup_count,
                        action_text="取票列表",
                    ),
                    build_summary_count(
                        icon="📋",
                        label="演出表",
                        count=show_count,
                        action_text="演出列表",
                    ),
                ],
            },
        ],
    }


# =========================================================
# 無待辦休息卡
# =========================================================

def build_rest_content():
    """
    今天完全沒有待辦時顯示。
    """

    return {
        "type": "box",
        "layout": "vertical",
        "paddingTop": "28px",
        "paddingBottom": "28px",
        "paddingStart": "16px",
        "paddingEnd": "16px",
        "backgroundColor": BODY_COLOR,
        "cornerRadius": "14px",
        "borderWidth": "1px",
        "borderColor": LINE_COLOR,
        "contents": [
            {
                "type": "text",
                "text": "☕",
                "size": "xxl",
                "align": "center",
            },
            {
                "type": "text",
                "text": "今天沒有任何待辦",
                "size": "md",
                "weight": "bold",
                "color": TEXT_COLOR,
                "align": "center",
                "margin": "md",
                "wrap": True,
            },
            {
                "type": "text",
                "text": (
                    "好好休息，"
                    "享受悠閒的一天～"
                ),
                "size": "sm",
                "color": LIGHT_TEXT_COLOR,
                "align": "center",
                "margin": "sm",
                "wrap": True,
            },
        ],
    }

# =========================================================
# 建立今日待辦卡片
# =========================================================

def build_today_card(today=None):
    """
    建立完整的「☀️ 今日待辦事項」Flex Message。
    """

    today = normalize_today(today)

    ticket_shows = sort_today_ticket_shows(
        get_today_ticket_shows(today)
    )

    pickup_shows = sort_today_pickup_shows(
        get_today_pickup_shows(today)
    )

    show_shows = sort_today_show_shows(
        get_today_show_shows(today)
    )

    total_count = (
        len(ticket_shows)
        + len(pickup_shows)
        + len(show_shows)
    )

    if total_count == 0:

        body_contents = [
            build_rest_content()
        ]

    else:

        body_contents = [
            build_summary(
                ticket_count=len(ticket_shows),
                pickup_count=len(pickup_shows),
                show_count=len(show_shows),
            )
        ]

        if ticket_shows:

            body_contents.append(
                build_section(
                    icon="🎟",
                    title="今日搶票",
                    items=ticket_shows,
                    item_builder=build_ticket_item,
                    empty_text="今天沒有需要搶票的演出",
                )
            )

        if pickup_shows:

            body_contents.append(
                build_section(
                    icon="📦",
                    title="今日取票",
                    items=pickup_shows,
                    item_builder=build_pickup_item,
                    empty_text="今天沒有需要取票的演出",
                )
            )

        if show_shows:

            body_contents.append(
                build_section(
                    icon="🎤",
                    title="今日演出",
                    items=show_shows,
                    item_builder=build_show_item,
                    empty_text="今天沒有舉行中的演出",
                )
            )

    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": build_header(today),
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

    return FlexSendMessage(
        alt_text="☀️ 今日待辦事項",
        contents=bubble,
    )


# =========================================================
# 相容舊函式名稱
# =========================================================

def create_today_card(today=None):
    """
    舊程式若使用 create_today_card()，
    可繼續直接呼叫。
    """

    return build_today_card(
        today
    )


def get_today_card(today=None):
    """
    舊程式若使用 get_today_card()，
    可繼續直接呼叫。
    """

    return build_today_card(
        today
    )