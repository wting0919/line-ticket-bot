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
    parse_datetime,
    parse_date,
)

from show_list import (
    get_all_shows,
)

from helpers import (
    get_current_shows,
    get_state,
    set_current_index,
)

from linebot.exceptions import LineBotApiError

import config


# =========================================================
# View Show V3
# 奶茶色系
# =========================================================

HEADER_COLOR = "#C9B29B"
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

FAILED_BACKGROUND_COLOR = "#F8E5E2"
FAILED_TEXT_COLOR = "#A05A4A"


# =========================================================
# 基本工具
# =========================================================

def safe_text(
    value,
    default="未設定",
):
    """
    安全處理空值。

    None、空字串或純空白時，
    回傳指定的預設文字。
    """

    if value is None:
        return default

    text = str(value).strip()

    if not text:
        return default

    return text


def remove_none_elements(value):
    """
    遞迴移除 Flex JSON 中的 None。

    避免 LINE 回傳：
    cannot contain null elements
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
    margin="md",
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
# 日期格式
# =========================================================

WEEKDAY_TEXT = [
    "一",
    "二",
    "三",
    "四",
    "五",
    "六",
    "日",
]


def format_datetime_with_weekday(value):
    """
    搶票時間格式：

    2026/08/15（六）13:00
    """

    if not value:
        return "未設定"

    parsed_value = parse_datetime(
        value
    )

    if parsed_value is None:
        return safe_text(
            format_datetime(value)
        )

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
    取票日期格式：

    2026/10/10（六）
    """

    if not value:
        return "未設定"

    parsed_value = parse_date(
        value
    )

    if parsed_value is None:
        return safe_text(value)

    if hasattr(
        parsed_value,
        "date",
    ):
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


# =========================================================
# 上一筆／下一筆 Quick Reply
# =========================================================

def view_navigation_quick_reply():
    """
    詳細卡片下方保留上一筆與下一筆。
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
# 狀態膠囊
# =========================================================

def build_status_tag(
    text,
    background_color,
    text_color,
):
    """
    建立三字狀態膠囊。
    """

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


def build_status_area(
    status,
    pickup_status,
):
    """
    狀態顯示規則：

    黃色：
        待搶票、未取票

    綠色：
        已搶票、已取票

    紅色：
        未搶到
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
# 共用資訊列
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
                "text": safe_text(icon, ""),
                "size": "sm",
                "flex": 0,
            },
            {
                "type": "text",
                "text": safe_text(label, ""),
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
    建立演出、搶票、取票資訊區塊。

    rows 格式：

    [
        ("📅", "演出日期", "2026/10/18（六）"),
        ("🕒", "搶票時間", "2026/08/15（六）13:00"),
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
                            "text": safe_text(
                                icon,
                                "",
                            ),
                            "size": "md",
                            "align": "center",
                        }
                    ],
                },
                {
                    "type": "text",
                    "text": safe_text(
                        title,
                        "",
                    ),
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
    flex=1,
):
    """
    自製奶茶色圓角按鈕。

    Box 元件支援 action，
    文字大小可自行控制。
    """

    return {
        "type": "box",
        "layout": "vertical",
        "flex": flex,
        "backgroundColor": BUTTON_COLOR,
        "cornerRadius": "10px",
        "paddingTop": "11px",
        "paddingBottom": "11px",
        "paddingStart": "3px",
        "paddingEnd": "3px",
        "justifyContent": "center",
        "alignItems": "center",
        "action": {
            "type": "message",
            "label": label,
            "text": action_text,
        },
        "contents": [
            {
                "type": "text",
                "text": label,
                "size": "xs",
                "weight": "bold",
                "color": WHITE_COLOR,
                "align": "center",
                "wrap": False,
            }
        ],
    }


def build_action_area(
    index,
    status,
    pickup_status,
):
    """
    建立底部操作按鈕。
    """

    main_buttons = [
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
    ]

    main_buttons = [
        button
        for button in main_buttons
        if button is not None
    ]

    contents = [
        build_separator(
            margin="xl",
        ),
        {
            "type": "box",
            "layout": "horizontal",
            "spacing": "xs",
            "margin": "lg",
            "contents": main_buttons,
        },
    ]

    if status == "等待搶票":

        ticket_buttons = [
            build_action_button(
                label="✅ 完成搶票",
                action_text=f"完成搶票 {index}",
            ),
            build_action_button(
                label="❌ 未搶到",
                action_text=f"未搶到 {index}",
            ),
        ]

        ticket_buttons = [
            button
            for button in ticket_buttons
            if button is not None
        ]

        contents.append(
            {
                "type": "box",
                "layout": "horizontal",
                "spacing": "xs",
                "margin": "sm",
                "contents": ticket_buttons,
            }
        )

    elif (
        status == "已搶票"
        and pickup_status != "已取票"
    ):

        pickup_buttons = [
            build_action_button(
                label="✅ 完成取票",
                action_text=f"完成取票 {index}",
            )
        ]

        pickup_buttons = [
            button
            for button in pickup_buttons
            if button is not None
        ]

        contents.append(
            {
                "type": "box",
                "layout": "horizontal",
                "margin": "sm",
                "contents": pickup_buttons,
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
        show.get(
            "演出日期",
            "",
        )
    )

    ticket_time = (
        format_datetime_with_weekday(
            show.get("搶票時間")
        )
    )

    platform = safe_text(
        show.get("售票平台")
    )

    price_quantity = format_price(
        show.get("價格張數")
    )

    pickup_date = (
        format_date_with_weekday(
            show.get("取票日期")
        )
    )

    pickup_person = safe_text(
        show.get("取票人")
    )

    ticket_master = safe_text(
        show.get("搶票大師")
    )

    note = show.get("備註")

    body_contents = [
        build_status_area(
            status=status,
            pickup_status=pickup_status,
        ),

        # =====================
        # 演出資訊
        # =====================

        build_detail_section(
            icon="📋",
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

        # =====================
        # 搶票資訊
        # =====================

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

    # =====================
    # 取票資訊
    # =====================

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
                            "👤",
                            "取票人員",
                            pickup_person,
                        ),
                    ],
                ),
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "md",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "width": "80px",
                            "height": "3px",
                            "backgroundColor": BUTTON_COLOR,
                            "cornerRadius": "2px",
                            "contents": [],
                        }
                    ],
                },
                build_info_row(
                    icon="🎯",
                    label="搶票大師",
                    value=ticket_master,
                    margin="md",
                ),
            ]
        )

    # =====================
    # 備註
    # =====================

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

    # =====================
    # 操作按鈕
    # =====================

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

        # =====================
        # Header
        # =====================

        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": HEADER_COLOR,
            "paddingTop": "16px",
            "paddingBottom": "16px",
            "paddingStart": "16px",
            "paddingEnd": "16px",
            "contents": [
                {
                    "type": "text",
                    "text": f"🎤 {show_name}",
                    "size": "md",
                    "weight": "bold",
                    "color": WHITE_COLOR,
                    "wrap": True,
                },
            ],
        },

        # =====================
        # Body
        # =====================

        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": BODY_COLOR,
            "paddingTop": "14px",
            "paddingBottom": "14px",
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

    bubble = remove_none_elements(
        bubble
    )

    return FlexSendMessage(
        alt_text=(
            f"🎤 {show_name}"
            "｜演出詳細"
        ),
        contents=bubble,
        quick_reply=(
            view_navigation_quick_reply()
        ),
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

        print(
            "[view_show] 準備送出 Flex：",
            show.get("演出名稱"),
            flush=True,
        )

        config.line_bot_api.reply_message(
            event.reply_token,
            message,
        )

        print(
            "[view_show] Flex 送出成功",
            flush=True,
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

    except LineBotApiError as error:

        print(
            "========== 查看 Flex LINE API 錯誤 ==========",
            flush=True,
        )

        print(
            "status_code：",
            getattr(error, "status_code", None),
            flush=True,
        )

        print(
            "request_id：",
            getattr(error, "request_id", None),
            flush=True,
        )

        print(
            "error_response：",
            getattr(error, "error_response", None),
            flush=True,
        )

        print(
            "完整錯誤：",
            repr(error),
            flush=True,
        )

        print(
            "=============================================",
            flush=True,
        )

        # 不要再次使用 event.reply_token
        return True

    except Exception as error:

        print(
            "========== 查看功能程式錯誤 ==========",
            flush=True,
        )

        print(
            "錯誤類型：",
            type(error).__name__,
            flush=True,
        )

        print(
            "錯誤內容：",
            repr(error),
            flush=True,
        )

        print(
            "=======================================",
            flush=True,
        )

        # 只有在尚未呼叫 reply_message 前發生的一般錯誤，
        # 才嘗試回覆使用者。
        try:
            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=(
                        "❌ 演出詳細資料載入失敗\n"
                        f"{type(error).__name__}: {error}"
                    )
                )
            )

        except LineBotApiError as reply_error:
            print(
                "錯誤訊息回覆失敗：",
                repr(reply_error),
                flush=True,
            )

        return True