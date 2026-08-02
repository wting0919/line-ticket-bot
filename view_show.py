from linebot.models import (
    TextSendMessage,
    FlexSendMessage,
    QuickReply,
    QuickReplyButton,
    MessageAction,
)

from utils import (
    format_price,
    format_datetime,
    format_show_dates,
)

from show_list import (
    get_all_shows,
)

from helpers import (
    get_current_shows,
    get_state,
    set_current_index,
)

import config


# =========================================================
# 奶茶色系
# =========================================================

HEADER_COLOR = "#C9B29B"
BODY_COLOR = "#FFFCF8"
SECTION_COLOR = "#F4ECE4"
TAG_COLOR = "#F1E8DE"

TEXT_COLOR = "#5C5148"
SUBTEXT_COLOR = "#75695F"
LIGHT_TEXT_COLOR = "#9A8D82"

LINE_COLOR = "#E7DDD2"

BUTTON_COLOR = "#B99F86"
DANGER_COLOR = "#B67C62"
SUCCESS_COLOR = "#879A7B"

WAITING_BACKGROUND_COLOR = "#FFF4D6"
WAITING_TEXT_COLOR = "#A87300"

SUCCESS_BACKGROUND_COLOR = "#E8F3E6"
SUCCESS_TEXT_COLOR = "#5B7D4A"

FAILED_BACKGROUND_COLOR = "#F8E5E2"
FAILED_TEXT_COLOR = "#A05A4A"

WHITE_COLOR = "#FFFFFF"


# =========================================================
# 基本工具
# =========================================================

def safe_text(value, default="未設定"):
    """
    安全處理空值。
    """

    if value is None:
        return default

    text = str(value).strip()

    if not text:
        return default

    return text


def build_separator(margin="md"):
    """
    建立奶茶色分隔線。
    """

    return {
        "type": "separator",
        "margin": margin,
        "color": LINE_COLOR,
    }


# =========================================================
# 上一筆／下一筆 Quick Reply
# =========================================================

def view_navigation_quick_reply():
    """
    詳細卡片底下保留上一筆與下一筆快捷按鈕。
    """

    return QuickReply(
        items=[
            QuickReplyButton(
                action=MessageAction(
                    label="⬅️ 上一筆",
                    text="上一筆",
                )
            ),
            QuickReplyButton(
                action=MessageAction(
                    label="➡️ 下一筆",
                    text="下一筆",
                )
            ),
        ]
    )


# =========================================================
# 狀態標籤
# =========================================================

def build_status_tag(
    text,
    background_color=TAG_COLOR,
    text_color=SUBTEXT_COLOR,
):
    """
    建立狀態膠囊。
    """

    return {
        "type": "box",
        "layout": "vertical",
        "backgroundColor": background_color,
        "cornerRadius": "12px",
        "paddingTop": "4px",
        "paddingBottom": "4px",
        "paddingStart": "10px",
        "paddingEnd": "10px",
        "contents": [
            {
                "type": "text",
                "text": safe_text(text, ""),
                "size": "xxs",
                "weight": "bold",
                "color": text_color,
                "align": "center",
                "wrap": False,
            }
        ],
    }


def build_status_area(
    status,
    pickup_status,
):
    """
    建立狀態膠囊。

    顯示文字統一為三個字：
    待搶票、已搶票、未搶到、未取票、已取票。
    """

    contents = []

    if status == "已搶票":

        contents.append(
            build_status_tag(
                text="已搶票",
                background_color=SUCCESS_BACKGROUND_COLOR,
                text_color=SUCCESS_TEXT_COLOR,
            )
        )

        if pickup_status == "已取票":

            contents.append(
                build_status_tag(
                    text="已取票",
                    background_color=SUCCESS_BACKGROUND_COLOR,
                    text_color=SUCCESS_TEXT_COLOR,
                )
            )

        else:

            contents.append(
                build_status_tag(
                    text="未取票",
                    background_color=WAITING_BACKGROUND_COLOR,
                    text_color=WAITING_TEXT_COLOR,
                )
            )

    elif status == "未搶到":

        contents.append(
            build_status_tag(
                text="未搶到",
                background_color=FAILED_BACKGROUND_COLOR,
                text_color=FAILED_TEXT_COLOR,
            )
        )

    else:

        contents.append(
            build_status_tag(
                text="待搶票",
                background_color=WAITING_BACKGROUND_COLOR,
                text_color=WAITING_TEXT_COLOR,
            )
        )

    return {
        "type": "box",
        "layout": "horizontal",
        "spacing": "sm",
        "margin": "md",
        "contents": contents,
    }

# =========================================================
# 資訊列
# =========================================================

def build_info_row(
    icon,
    label,
    value,
):
    """
    建立單筆資訊列。
    """

    return {
        "type": "box",
        "layout": "horizontal",
        "margin": "sm",
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


# =========================================================
# 共用資訊區塊
# =========================================================

def build_detail_section(
    icon,
    title,
    rows,
    margin="lg",
):
    """
    建立演出、搶票、取票等資訊區塊。

    rows 格式：

    [
        ("📅", "演出日期", "2026/10/18"),
        ("🕒", "搶票時間", "2026/08/15 13:00"),
    ]
    """

    contents = [
        {
            "type": "box",
            "layout": "horizontal",
            "alignItems": "center",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "width": "34px",
                    "height": "34px",
                    "backgroundColor": SECTION_COLOR,
                    "cornerRadius": "17px",
                    "justifyContent": "center",
                    "alignItems": "center",
                    "contents": [
                        {
                            "type": "text",
                            "text": icon,
                            "size": "md",
                            "align": "center",
                        }
                    ],
                },
                {
                    "type": "text",
                    "text": title,
                    "size": "md",
                    "weight": "bold",
                    "color": TEXT_COLOR,
                    "margin": "sm",
                    "flex": 1,
                    "wrap": True,
                },
            ],
        }
    ]

    for row_icon, label, value in rows:
        contents.append(
            build_info_row(
                icon=row_icon,
                label=label,
                value=value,
            )
        )

    return {
        "type": "box",
        "layout": "vertical",
        "margin": margin,
        "contents": contents,
    }


# =========================================================
# 備註區塊
# =========================================================

def build_note_section(note):
    """
    建立備註區塊。
    """

    return {
        "type": "box",
        "layout": "vertical",
        "margin": "lg",
        "contents": [
            {
                "type": "box",
                "layout": "horizontal",
                "alignItems": "center",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "width": "34px",
                        "height": "34px",
                        "backgroundColor": SECTION_COLOR,
                        "cornerRadius": "17px",
                        "justifyContent": "center",
                        "alignItems": "center",
                        "contents": [
                            {
                                "type": "text",
                                "text": "📝",
                                "size": "md",
                                "align": "center",
                            }
                        ],
                    },
                    {
                        "type": "text",
                        "text": "備註",
                        "size": "md",
                        "weight": "bold",
                        "color": TEXT_COLOR,
                        "margin": "sm",
                    },
                ],
            },
            {
                "type": "box",
                "layout": "vertical",
                "margin": "md",
                "paddingAll": "12px",
                "backgroundColor": SECTION_COLOR,
                "cornerRadius": "10px",
                "contents": [
                    {
                        "type": "text",
                        "text": safe_text(
                            note,
                            "無",
                        ),
                        "size": "sm",
                        "color": TEXT_COLOR,
                        "wrap": True,
                    }
                ],
            },
        ],
    }


# =========================================================
# 操作按鈕
# =========================================================

def build_action_button(
    label,
    action_text,
    style="secondary",
    color=None,
    flex=1,
):
    """
    建立操作按鈕。
    """

    button = {
        "type": "button",
        "style": style,
        "height": "sm",
        "flex": flex,
        "action": {
            "type": "message",
            "label": label,
            "text": action_text,
        },
    }

    if color:
        button["color"] = color

    return button


def build_action_area(
    index,
    status,
    pickup_status,
):
    """
    建立底部操作按鈕。
    """

    contents = [
        build_separator(
            margin="xl",
        ),
        {
            "type": "box",
            "layout": "horizontal",
            "spacing": "sm",
            "margin": "lg",
            "contents": [
                build_action_button(
                    label="✏️ 修改",
                    action_text=f"修改 {index}",
                ),
                build_action_button(
                    label="📄 複製",
                    action_text=f"複製 {index}",
                ),
                build_action_button(
                    label="🗑️ 刪除",
                    action_text=f"刪除 {index}",
                ),
            ],
        },
    ]

    if status == "等待搶票":

        contents.append(
            {
                "type": "box",
                "layout": "horizontal",
                "spacing": "sm",
                "margin": "sm",
                "contents": [
                    build_action_button(
                        label="✅ 完成搶票",
                        action_text=f"完成搶票 {index}",
                        style="primary",
                        color=SUCCESS_COLOR,
                    ),
                    build_action_button(
                        label="❌ 未搶到",
                        action_text=f"未搶到 {index}",
                        style="primary",
                        color=DANGER_COLOR,
                    ),
                ],
            }
        )

    elif (
        status == "已搶票"
        and pickup_status != "已取票"
    ):

        contents.append(
            {
                "type": "box",
                "layout": "horizontal",
                "margin": "sm",
                "contents": [
                    build_action_button(
                        label="✅ 完成取票",
                        action_text=f"完成取票 {index}",
                        style="primary",
                        color=SUCCESS_COLOR,
                    ),
                ],
            }
        )

    return contents


# =========================================================
# 建立演出詳細 Flex
# =========================================================

def build_view_show_card(
    show,
    index,
):
    """
    建立完整演出詳細卡片。
    """

    show_name = safe_text(
        show.get("演出名稱"),
        "未命名演出",
    )

    status = show.get(
        "搶票狀態",
        "等待搶票",
    )

    pickup_status = show.get(
        "取票狀態",
        "未取票",
    )

    show_dates = format_show_dates(
        show.get("演出日期", "")
    )

    ticket_time = format_datetime(
        show.get("搶票時間", "")
    )

    platform = safe_text(
        show.get("售票平台")
    )

    price_quantity = format_price(
        show.get("價格張數")
    )

    pickup_date = safe_text(
        show.get("取票日期")
    )

    ticket_master = safe_text(
        show.get("搶票大師")
    )

    pickup_person = safe_text(
        show.get("取票人")
    )

    note = show.get("備註")

    body_contents = [
        build_status_area(
            status=status,
            pickup_status=pickup_status,
        ),
        build_detail_section(
            icon="🎤",
            title="演出資訊",
            rows=[
                (
                    "📅",
                    "演出日期",
                    show_dates,
                ),
            ],
        ),
        build_separator(
            margin="lg",
        ),
        build_detail_section(
            icon="🎟",
            title="搶票資訊",
            rows=[
                (
                    "🕒",
                    "搶票時間",
                    ticket_time,
                ),
                (
                    "🏢",
                    "售票平台",
                    platform,
                ),
                (
                    "💰",
                    "價格張數",
                    price_quantity,
                ),
            ],
        ),
    ]

    if status == "已搶票":

        body_contents.extend(
            [
                build_separator(
                    margin="lg",
                ),
                build_detail_section(
                    icon="📦",
                    title="取票資訊",
                    rows=[
                        (
                            "📅",
                            "取票日期",
                            pickup_date,
                        ),
                        (
                            "🎯",
                            "搶票大師",
                            ticket_master,
                        ),
                        (
                            "👤",
                            "取票人",
                            pickup_person,
                        ),
                    ],
                ),
            ]
        )

    if note:
        body_contents.extend(
            [
                build_separator(
                    margin="lg",
                ),
                build_note_section(
                    note
                ),
            ]
        )

    body_contents.extend(
        build_action_area(
            index=index,
            status=status,
            pickup_status=pickup_status,
        )
    )

    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": HEADER_COLOR,
            "paddingTop": "18px",
            "paddingBottom": "18px",
            "paddingStart": "18px",
            "paddingEnd": "18px",
            "contents": [
                {
                    "type": "text",
                    "text": f"🎤 {show_name}",
                    "size": "xl",
                    "weight": "bold",
                    "color": WHITE_COLOR,
                    "wrap": True,
                },
                {
                    "type": "text",
                    "text": f"演出詳細資料・第 {index} 筆",
                    "size": "xs",
                    "color": "#FFF9F3",
                    "margin": "sm",
                    "wrap": True,
                },
            ],
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": BODY_COLOR,
            "paddingTop": "14px",
            "paddingBottom": "18px",
            "paddingStart": "16px",
            "paddingEnd": "16px",
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
        alt_text=f"🎤 {show_name}｜演出詳細",
        contents=bubble,
        quick_reply=view_navigation_quick_reply(),
    )


# =========================================================
# 查看功能
# =========================================================

def handle_view_show(
    event,
    text,
    user_id,
):
    """
    處理「查看 1」指令。
    """

    state = get_state(
        user_id
    )

    shows = get_current_shows(
        user_id
    )

    if shows is None:
        shows = get_all_shows()

    shows = shows or []

    try:

        index = (
            int(
                text.replace(
                    "查看",
                    "",
                ).strip()
            )
            - 1
        )

        if (
            index < 0
            or index >= len(shows)
        ):

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="❌ 找不到這筆演出"
                )
            )

            return True

        show = shows[index]

        if isinstance(
            state,
            dict,
        ):
            set_current_index(
                user_id,
                index,
            )

        message = build_view_show_card(
            show=show,
            index=index + 1,
        )

        config.line_bot_api.reply_message(
            event.reply_token,
            message,
        )

        return True

    except ValueError:

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="請輸入格式：\n查看 1"
            )
        )

        return True

    except Exception as error:

        print(
            "查看錯誤：",
            repr(error),
            flush=True,
        )

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=(
                    "❌ 演出詳細資料載入失敗\n"
                    f"{type(error).__name__}: {error}"
                )
            )
        )

        return True