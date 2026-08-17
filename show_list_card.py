from math import ceil

from linebot.models import FlexSendMessage

from theme import (
    BODY_COLOR,
    CARD_COLOR,
    SECTION_COLOR,
    TEXT_COLOR,
    SUBTEXT_COLOR,
    LIGHT_TEXT_COLOR,
    LINE_COLOR,
    BUTTON_COLOR,
    WHITE_COLOR,
    WAITING_BACKGROUND_COLOR,
    WAITING_TEXT_COLOR,
    SUCCESS_BACKGROUND_COLOR,
    SUCCESS_TEXT_COLOR,
    FAILED_BACKGROUND_COLOR,
    FAILED_TEXT_COLOR,
    build_brand_header,
    safe_text,
    remove_none_elements,
    build_activity_badge,
)

from utils import (
    format_datetime,
    format_date,
    format_show_dates_inline,
    format_price,
)


# =========================================================
# Show List Card V1
# TicketCat 共用列表卡
# =========================================================

ITEMS_PER_PAGE = 8


# =========================================================
# 模式設定
# =========================================================

LIST_CONFIG = {
    "all": {
        "icon": "📋",
        "title": "演出列表",
        "empty_text": "目前沒有演出資料",
        "command": "演出列表",
    },
    "ticket": {
        "icon": "🎟",
        "title": "搶票列表",
        "empty_text": "目前沒有待搶票演出",
        "command": "搶票列表",
    },
    "pickup": {
        "icon": "📦",
        "title": "取票列表",
        "empty_text": "目前沒有取票資料",
        "command": "取票列表",
    },
}


def get_list_config(mode):
    """
    取得列表模式設定。
    """

    return LIST_CONFIG.get(
        mode,
        LIST_CONFIG["all"],
    )


# =========================================================
# 基本工具
# =========================================================

def normalize_page(
    page,
    total_pages,
):
    """
    將頁碼限制在有效範圍內。
    """

    try:
        page = int(page)

    except (TypeError, ValueError):
        page = 1

    if total_pages <= 0:
        return 1

    return max(
        1,
        min(page, total_pages),
    )


def get_page_items(
    shows,
    page,
):
    """
    取得指定頁面的資料。
    """

    safe_shows = shows or []

    total_count = len(safe_shows)

    total_pages = max(
        1,
        ceil(total_count / ITEMS_PER_PAGE),
    )

    page = normalize_page(
        page,
        total_pages,
    )

    start_index = (
        page - 1
    ) * ITEMS_PER_PAGE

    end_index = (
        start_index
        + ITEMS_PER_PAGE
    )

    return (
        safe_shows[start_index:end_index],
        page,
        total_pages,
        start_index,
    )


def get_show_action_text(
    show,
    display_index,
):
    """
    優先使用 Supabase id 查看詳細。

    若沒有 id，退回「查看 N」。
    """

    show_id = str(
        show.get("id") or ""
    ).strip()

    if show_id:
        return f"查看ID {show_id}"

    return f"查看 {display_index}"


# =========================================================
# 狀態膠囊
# =========================================================

def build_list_status_tag(
    text,
    background_color,
    text_color,
):
    """
    建立列表用的小型狀態膠囊。
    """

    return {
        "type": "box",
        "layout": "vertical",
        "backgroundColor": background_color,
        "cornerRadius": "9px",
        "paddingTop": "4px",
        "paddingBottom": "4px",
        "paddingStart": "9px",
        "paddingEnd": "9px",
        "flex": 0,
        "contents": [
            {
                "type": "text",
                "text": safe_text(
                    text,
                    "",
                ),
                "size": "xxs",
                "weight": "bold",
                "color": text_color,
                "align": "center",
                "wrap": False,
            }
        ],
    }


def build_ticket_status_tag(show):
    """
    建立搶票狀態。
    """

    status = safe_text(
        show.get("搶票狀態"),
        "待搶票",
    )

    if status == "已搶票":

        return build_list_status_tag(
            text="已搶票",
            background_color=SUCCESS_BACKGROUND_COLOR,
            text_color=SUCCESS_TEXT_COLOR,
        )

    if status == "未搶到":

        return build_list_status_tag(
            text="未搶到",
            background_color=FAILED_BACKGROUND_COLOR,
            text_color=FAILED_TEXT_COLOR,
        )

    return build_list_status_tag(
        text="待搶票",
        background_color=WAITING_BACKGROUND_COLOR,
        text_color=WAITING_TEXT_COLOR,
    )


def build_pickup_status_tag(show):
    """
    建立取票狀態。
    """

    status = safe_text(
        show.get("取票狀態"),
        "未取票",
    )

    if status == "已取票":

        return build_list_status_tag(
            text="已取票",
            background_color=SUCCESS_BACKGROUND_COLOR,
            text_color=SUCCESS_TEXT_COLOR,
        )

    return build_list_status_tag(
        text="未取票",
        background_color=WAITING_BACKGROUND_COLOR,
        text_color=WAITING_TEXT_COLOR,
    )

# =========================================================
# 資訊列
# =========================================================

def build_compact_info_row(
    icon,
    value,
    margin="xs",
):
    """
    建立列表中的精簡資訊列。
    """

    return {
        "type": "box",
        "layout": "horizontal",
        "margin": margin,
        "alignItems": "flex-start",
        "contents": [
            {
                "type": "text",
                "text": safe_text(
                    icon,
                    "",
                ),
                "size": "xs",
                "flex": 0,
            },
            {
                "type": "text",
                "text": safe_text(value),
                "size": "xs",
                "color": SUBTEXT_COLOR,
                "margin": "sm",
                "flex": 1,
                "wrap": True,
            },
        ],
    }


def build_status_area(
    show,
    mode,
):
    """
    依列表類型建立狀態區。
    """

    tags = []

    if mode == "ticket":

        tags.append(
            build_ticket_status_tag(show)
        )

    elif mode == "pickup":

        tags.append(
            build_pickup_status_tag(show)
        )

    else:

        tags.append(
            build_ticket_status_tag(show)
        )

        ticket_status = safe_text(
            show.get("搶票狀態"),
            "待搶票",
        )

        if ticket_status == "已搶票":

            tags.append(
                build_pickup_status_tag(show)
            )

    return {
        "type": "box",
        "layout": "horizontal",
        "spacing": "xs",
        "contents": tags,
    }

def append_row(
    rows,
    icon,
    value,
    formatter=None,
):
    """
    有值才加入資訊列。
    """

    if not value:
        return

    if formatter:
        value = formatter(value)

    rows.append(
        build_compact_info_row(
            icon=icon,
            value=value,
        )
    )

def format_reminders(reminder):
    """
    將提醒事項格式化為項目符號。
    """

    if not reminder:
        return ""

    return "\n".join(
        f"• {line.strip()}"
        for line in reminder.splitlines()
        if line.strip()
    )


# =========================================================
# 各類列表內容
# =========================================================

def build_all_show_rows(show):
    """
    演出列表顯示欄位。
    """

    rows = [
        build_compact_info_row(
            icon="📅",
            value=format_show_dates_inline(
                show.get("演出日期")
            ),
            margin="sm",
        ),
    ]

    append_row(
        rows,
        "🪪",
        show.get("會員資訊"),
    )

    reminder = format_reminders(
        show.get("提醒事項")
    )

    append_row(
        rows,
        "🔔",
        reminder,
    )

    return rows


def build_ticket_show_rows(show):
    """
    搶票列表顯示欄位。
    """

    rows = [
        build_compact_info_row(
            icon="🕒",
            value=format_datetime(
                show.get("搶票時間")
            ),
            margin="sm",
        ),
        build_compact_info_row(
            icon="🌐",
            value=safe_text(
                show.get("售票平台")
            ),
        ),
    ]

    append_row(
        rows,
        "💰",
        show.get("價格張數"),
        format_price,
    )

    append_row(
        rows,
        "🪪",
        show.get("會員資訊"),
    )

    reminder = format_reminders(
        show.get("提醒事項")
    )

    append_row(
        rows,
        "🔔",
        reminder,
    )

    append_row(
        rows,
        "📝",
        show.get("備註"),
    )

    return rows

def build_pickup_show_rows(show):
    """
    取票列表顯示欄位。
    """

    rows = [
        build_compact_info_row(
            icon="📅",
            value=format_date(
                show.get("取票日期")
            ),
            margin="sm",
        ),
        build_compact_info_row(
            icon="👤",
            value=(
                "取票人員："
                f"{safe_text(show.get('取票人'))}"
            ),
        ),
    ]

    append_row(
        rows,
        "🎯",
        (
            f"搶票大師："
            f"{safe_text(show.get('搶票大師'))}"
        )
        if show.get("搶票大師")
        else "",
    )

    return rows


def get_item_rows(
    show,
    mode,
):
    """
    依模式取得列表欄位。
    """

    if mode == "ticket":
        return build_ticket_show_rows(show)

    if mode == "pickup":
        return build_pickup_show_rows(show)

    return build_all_show_rows(show)


# =========================================================
# 單筆列表項目
# =========================================================

def build_show_list_item(
    show,
    mode,
    display_index,
):
    """
    建立可點擊的單筆演出資料。
    """

    artist = safe_text(
        show.get("藝人"),
        show.get("演出名稱"),
    )

    activity_name = (
        show.get("活動名稱") or ""
    ).strip()

    action_text = get_show_action_text(
        show=show,
        display_index=display_index,
    )

    contents = [
        {
            "type": "box",
            "layout": "horizontal",
            "alignItems": "center",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "width": "25px",
                    "height": "25px",
                    "backgroundColor": BUTTON_COLOR,
                    "cornerRadius": "13px",
                    "justifyContent": "center",
                    "alignItems": "center",
                    "flex": 0,
                    "contents": [
                        {
                            "type": "text",
                            "text": str(display_index),
                            "size": "xxs",
                            "weight": "bold",
                            "color": WHITE_COLOR,
                            "align": "center",
                        }
                    ],
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "xs",
                    "flex": 1,
                    "contents": [

                        build_activity_badge(
                            safe_text(show.get("活動"))
                        ),

                        {
                            "type": "text",
                            "text": artist,
                            "size": "sm",
                            "weight": "bold",
                            "color": TEXT_COLOR,
                            "margin": "sm",
                            "wrap": True,
                        },

                        *(
                            [{
                                "type": "text",
                                "text": activity_name,
                                "size": "xxs",
                                "color": SUBTEXT_COLOR,
                                "margin": "2px",
                                "wrap": True,
                            }]
                            if activity_name
                            else []
                        ),
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
                    "margin": "sm",
                },
            ],
        }
    ]

    contents.extend(
        get_item_rows(
            show=show,
            mode=mode,
        )
    )

    contents.append(
        {
            "type": "box",
            "layout": "horizontal",
            "margin": "sm",
            "contents": [
                build_status_area(
                    show=show,
                    mode=mode,
                )
            ],
        }
    )

    return {
        "type": "box",
        "layout": "vertical",
        "backgroundColor": CARD_COLOR,
        "cornerRadius": "12px",
        "borderWidth": "1px",
        "borderColor": LINE_COLOR,
        "paddingTop": "14px",
        "paddingBottom": "14px",
        "paddingStart": "13px",
        "paddingEnd": "13px",
        "action": {
            "type": "message",
            "label": "查看詳細",
            "text": action_text,
        },
        "contents": contents,
    }

# =========================================================
# 空白狀態
# =========================================================

def build_empty_list(
    mode,
):
    """
    建立沒有資料時的畫面。
    """

    config = get_list_config(mode)

    return {
        "type": "box",
        "layout": "vertical",
        "backgroundColor": SECTION_COLOR,
        "cornerRadius": "12px",
        "paddingTop": "24px",
        "paddingBottom": "24px",
        "paddingStart": "14px",
        "paddingEnd": "14px",
        "contents": [
            {
                "type": "text",
                "text": "🐱",
                "size": "xxl",
                "align": "center",
            },
            {
                "type": "text",
                "text": config["empty_text"],
                "size": "sm",
                "weight": "bold",
                "color": TEXT_COLOR,
                "align": "center",
                "margin": "md",
                "wrap": True,
            },
        ],
    }


# =========================================================
# 分頁按鈕
# =========================================================

def build_page_button(
    label,
    command,
    enabled=True,
):
    """
    建立上一頁／下一頁按鈕。
    """

    if not enabled:

        return {
            "type": "box",
            "layout": "vertical",
            "flex": 1,
            "backgroundColor": SECTION_COLOR,
            "cornerRadius": "9px",
            "paddingTop": "8px",
            "paddingBottom": "8px",
            "contents": [
                {
                    "type": "text",
                    "text": label,
                    "size": "xxs",
                    "weight": "bold",
                    "color": LIGHT_TEXT_COLOR,
                    "align": "center",
                }
            ],
        }

    return {
        "type": "box",
        "layout": "vertical",
        "flex": 1,
        "backgroundColor": BUTTON_COLOR,
        "cornerRadius": "9px",
        "paddingTop": "8px",
        "paddingBottom": "8px",
        "action": {
            "type": "message",
            "label": label,
            "text": command,
        },
        "contents": [
            {
                "type": "text",
                "text": label,
                "size": "xxs",
                "weight": "bold",
                "color": WHITE_COLOR,
                "align": "center",
            }
        ],
    }


def build_pagination(
    mode,
    page,
    total_pages,
    command=None,
):
    """
    建立列表翻頁區。
    """

    config = get_list_config(mode)

    base_command = command or config["command"]

    previous_command = (
        f"{base_command} 第{page-1}頁"
    )

    next_command = (
        f"{base_command} 第{page+1}頁"
    )

    return {
        "type": "box",
        "layout": "horizontal",
        "spacing": "sm",
        "margin": "md",
        "alignItems": "center",
        "contents": [
            build_page_button(
                label="‹ 上一頁",
                command=previous_command,
                enabled=page > 1,
            ),
            {
                "type": "text",
                "text": (
                    f"第 {page} / "
                    f"{total_pages} 頁"
                ),
                "size": "xxs",
                "weight": "bold",
                "color": SUBTEXT_COLOR,
                "align": "center",
                "flex": 1,
                "wrap": False,
            },
            build_page_button(
                label="下一頁 ›",
                command=next_command,
                enabled=page < total_pages,
            ),
        ],
    }


# =========================================================
# 建立列表卡片
# =========================================================

def build_show_list_card(
    shows,
    mode="all",
    page=1,
    command=None,
):
    """
    建立 TicketCat 共用列表卡。

    mode：
        all
        ticket
        pickup
    """

    safe_shows = shows or []

    config = get_list_config(mode)

    (
        page_items,
        page,
        total_pages,
        start_index,
    ) = get_page_items(
        shows=safe_shows,
        page=page,
    )

    body_contents = []

    if not page_items:

        body_contents.append(
            build_empty_list(mode)
        )

    else:

        for local_index, show in enumerate(
            page_items,
            start=1,
        ):

            display_index = (
                start_index
                + local_index
            )

            body_contents.append(
                build_show_list_item(
                    show=show,
                    mode=mode,
                    display_index=display_index,
                )
            )

    if safe_shows and total_pages > 1:

        body_contents.append(
            build_pagination(
                mode=mode,
                page=page,
                total_pages=total_pages,
                command=command,
            )
        )

    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": build_brand_header(
            subtitle=None,
            message=(
                f"{config['icon']} "
                f"{config['title']}・"
                f"共 {len(safe_shows)} 筆"
            ),
            logo_size=44,
            compact=True,
        ),
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "backgroundColor": BODY_COLOR,
            "paddingTop": "12px",
            "paddingBottom": "12px",
            "paddingStart": "12px",
            "paddingEnd": "12px",
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
        alt_text=(
            f"{config['icon']} "
            f"{config['title']}"
        ),
        contents=bubble,
    )


# =========================================================
# 解析頁碼
# =========================================================

def parse_list_page(
    text,
    default_page=1,
):
    """
    支援：

    演出列表
    演出列表 第2頁
    搶票列表 第3頁
    """

    if "第" not in text:
        return default_page

    try:

        page_text = (
            text.split("第", 1)[1]
            .split("頁", 1)[0]
            .strip()
        )

        return max(
            1,
            int(page_text),
        )

    except (ValueError, IndexError):
        return default_page