from linebot.models import (
    TextSendMessage,
    FlexSendMessage,
    QuickReply,
    QuickReplyButton,
    MessageAction,
)

from linebot.exceptions import LineBotApiError

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

from theme import (
    BODY_COLOR,
    SECTION_COLOR,
    TEXT_COLOR,
    SUBTEXT_COLOR,
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
    build_separator,
    build_status_tag,
    build_activity_badge_row,
)

import config


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
# 日期格式
# =========================================================

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
    """
    建立共用欄位資訊。
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
                "size": "sm",
                "flex": 0,
            },
            {
                "type": "text",
                "text": safe_text(
                    label,
                    "",
                ),
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
    margin="md",
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
                    "width": "30px",
                    "height": "30px",
                    "backgroundColor": SECTION_COLOR,
                    "cornerRadius": "15px",
                    "justifyContent": "center",
                    "alignItems": "center",
                    "contents": [
                        {
                            "type": "text",
                            "text": safe_text(
                                icon,
                                "",
                            ),
                            "size": "sm",
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
# 提醒事項區塊
# =========================================================

def build_reminder_section(
    reminders,
):
    """
    建立提醒事項區塊。
    """

    if not reminders:
        return None

    reminder_text = "\n".join(
        f"• {item.strip()}"
        for item in reminders.splitlines()
        if item.strip()
    )

    return {
        "type": "box",
        "layout": "vertical",
        "margin": "md",
        "contents": [
            {
                "type": "box",
                "layout": "horizontal",
                "alignItems": "center",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "width": "30px",
                        "height": "30px",
                        "backgroundColor": SECTION_COLOR,
                        "cornerRadius": "15px",
                        "justifyContent": "center",
                        "alignItems": "center",
                        "contents": [
                            {
                                "type": "text",
                                "text": "🔔",
                                "size": "sm",
                                "align": "center",
                            }
                        ],
                    },
                    {
                        "type": "text",
                        "text": "注意事項",
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
                "margin": "sm",
                "paddingAll": "10px",
                "backgroundColor": SECTION_COLOR,
                "cornerRadius": "10px",
                "contents": [
                    {
                        "type": "text",
                        "text": reminder_text,
                        "size": "xxs",
                        "color": TEXT_COLOR,
                        "wrap": True,
                    }
                ],
            },
        ],
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
        "margin": "md",
        "contents": [
            {
                "type": "box",
                "layout": "horizontal",
                "alignItems": "center",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "width": "30px",
                        "height": "30px",
                        "backgroundColor": SECTION_COLOR,
                        "cornerRadius": "15px",
                        "justifyContent": "center",
                        "alignItems": "center",
                        "contents": [
                            {
                                "type": "text",
                                "text": "📝",
                                "size": "sm",
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
                "margin": "sm",
                "paddingAll": "10px",
                "backgroundColor": SECTION_COLOR,
                "cornerRadius": "10px",
                "contents": [
                    {
                        "type": "text",
                        "text": safe_text(note),
                        "size": "xxs",
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
    建立奶茶色圓角按鈕。
    """

    return {
        "type": "box",
        "layout": "vertical",
        "flex": flex,
        "backgroundColor": BUTTON_COLOR,
        "cornerRadius": "10px",
        "paddingTop": "10px",
        "paddingBottom": "10px",
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
    show,
    status,
    pickup_status,
):
    """
    建立卡片底部操作區。
    """

    main_buttons = [
        build_action_button(
            label="✏️ 修改",
            action_text=f"修改ID {show['id']}",
        ),
        build_action_button(
            label="📄 複製",
            action_text=f"複製ID {show['id']}",
        ),
        build_action_button(
            label="🗑️ 刪除",
            action_text=f"刪除ID {show['id']}",
        ),
    ]

    contents = [
        build_separator(
            margin="xl",
        ),
        {
            "type": "box",
            "layout": "horizontal",
            "spacing": "xs",
            "margin": "md",
            "contents": main_buttons,
        },
    ]

    if status == "待搶票":

        contents.append(
            {
                "type": "box",
                "layout": "horizontal",
                "spacing": "xs",
                "margin": "sm",
                "contents": [
                    build_action_button(
                        label="✅ 完成搶票",
                        action_text=f"完成搶票ID {show['id']}",
                    ),
                    build_action_button(
                        label="❌ 未搶到",
                        action_text=f"未搶到ID {show['id']}",
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
                        action_text=f"完成取票ID {show['id']}",
                    )
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

    artist = safe_text(
        show.get("藝人"),
    )

    activity = safe_text(
        show.get("活動"),
    )

    activity_name = (
        show.get("活動名稱") or ""
    ).strip()

    status = show.get(
        "搶票狀態",
        "待搶票",
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

    ticket_time = format_datetime_with_weekday(
        show.get("搶票時間")
    )

    platform = safe_text(
        show.get("售票平台")
    )

    price_quantity = format_price(
        show.get("價格張數")
    )

    member = safe_text(
        show.get("會員資訊")
    )

    sale_stage = safe_text(
        show.get("售票階段")
    )

    reminders = (
        show.get("注意事項") or ""
    ).strip()

    pickup_date = format_date_with_weekday(
        show.get("取票日期")
    )

    pickup_person = safe_text(
        show.get("取票人")
    )

    ticket_master = safe_text(
        show.get("搶票大師")
    )

    note = show.get("備註")


    body_contents = [

        build_activity_badge_row(activity),

        {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": artist,
                    "size": "lg",
                    "weight": "bold",
                    "color": TEXT_COLOR,
                    "wrap": True,
                },
                *(
                    [{
                        "type": "text",
                        "text": activity_name,
                        "size": "sm",
                        "color": SUBTEXT_COLOR,
                        "margin": "xs",
                        "wrap": True,
                    }]
                    if activity_name
                    else []
                ),
            ],
        },

        build_status_area(
            status=status,
            pickup_status=pickup_status,
        ),

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
            margin="md",
        ),

        build_separator(
            margin="md",
        ),

        build_detail_section(
            icon="🎟️",
            title="搶票資訊",
            rows=[
            (
                "🕒",
                "搶票時間",
                ticket_time,
            ),
            (
                "🌐",
                "售票平台",
                platform,
            ),
            (
                "💰",
                "價格張數",
                price_quantity,
            ),
            *(
                [
                    (
                        "🚩",
                        "售票階段",
                        sale_stage,
                    )
                ]
                if sale_stage
                else []
            ),
            *(
                [
                    (
                        "🔑",
                        "會員資訊",
                        member,
                    )
                ]
                if member
                else []
            ),
            margin="md",
        ),
    ]


    if reminders:

        body_contents.extend(
            [
                build_separator(
                    margin="md",
                ),
                build_reminder_section(
                    reminders
                ),
            ]
        )


    if status == "已搶票":

        body_contents.extend(
            [
                build_separator(
                    margin="md",
                ),
                build_detail_section(
                    icon="📦",
                    title="取票資訊",
                    rows=[
                        *(
                            [
                                (
                                    "📅",
                                    "取票日期",
                                    pickup_date,
                                )
                            ]
                            if show.get("取票日期")
                            else []
                        ),

                        *(
                            [
                                (
                                    "👤",
                                    "取票人員",
                                    pickup_person,
                                )
                            ]
                            if pickup_person
                            else []
                        ),

                        *(
                            [
                                (
                                    "🎯",
                                    "搶票大師",
                                    ticket_master,
                                )
                            ]
                            if ticket_master
                            else []
                        ),
                    ]
                ),
            ]
        )


    if note:

        body_contents.extend(
            [
                build_separator(
                    margin="md",
                ),
                build_note_section(note),
            ]
        )

    body_contents.extend(
        build_action_area(
            show=show,
            status=status,
            pickup_status=pickup_status,
        )
    )


    bubble = {
        "type": "bubble",
        "size": "mega",

        "header": build_brand_header(
            subtitle=None,
            message="演出詳細",
            logo_size=44,
            compact=True,
        ),

        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": BODY_COLOR,
            "paddingTop": "12px",
            "paddingBottom": "12px",
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
            f"🎤 {artist}"
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
    支援：

    查看ID 1
    """

    state = get_state(
        user_id
    )

    current_shows = get_current_shows(
        user_id
    )

    if current_shows is None:

        current_shows = get_all_shows()

    current_shows = current_shows or []

    try:

        if text.startswith("查看ID"):

            show_id = text.replace(
                "查看ID",
                "",
                1,
            ).strip()

            shows = get_all_shows() or []

            matched_index = None

            for current_index, current_show in enumerate(
                shows
            ):

                current_show_id = str(
                    current_show.get(
                        "id",
                        "",
                    )
                ).strip()

                if current_show_id == show_id:

                    matched_index = current_index
                    break

            if matched_index is None:

                config.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="❌ 找不到這筆演出"
                    )
                )

                return True

            index = matched_index

        else:

            shows = current_shows

            index = (
                int(
                    text.replace(
                        "查看",
                        "",
                        1,
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
                text="請輸入格式：\n查看ID 1"
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
            getattr(
                error,
                "status_code",
                None,
            ),
            flush=True,
        )

        print(
            "request_id：",
            getattr(
                error,
                "request_id",
                None,
            ),
            flush=True,
        )

        print(
            "error_response：",
            getattr(
                error,
                "error_response",
                None,
            ),
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

        # reply token 可能已經使用，
        # 不要在這裡再次回覆。
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

        try:

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=(
                        "❌ 演出詳細資料載入失敗\n"
                        f"{type(error).__name__}: "
                        f"{error}"
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