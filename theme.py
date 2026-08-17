import config


from ui import simple_quick_reply


def activity_quick_reply(
    include_cancel=True,
):
    buttons = ACTIVITY_OPTIONS.copy()

    if include_cancel:
        buttons.append(
            ("❌ 取消", "取消")
        )

    return simple_quick_reply(buttons)

def reminder_quick_reply(
    include_cancel=True,
):

    buttons = [
        (item, item)
        for item in REMINDER_OPTIONS
    ]

    buttons.extend(
        [
            ("✏️ 自訂", "自訂提醒"),
            ("✅ 完成", "完成提醒"),
            ("➖ 略過", "略過"),
        ]
    )

    if include_cancel:

        buttons.append(
            ("❌ 取消", "取消")
        )

    return simple_quick_reply(
        buttons
    )


def reminder_message(
    selected,
):

    if selected:

        selected_text = "\n".join(
            f"• {item}"
            for item in selected
        )

    else:

        selected_text = "（尚未選擇）"

    return (
        "🔔 提醒事項\n\n"
        "請選擇提醒事項\n\n"
        f"{selected_text}"
    )


REMINDER_OPTIONS = [
    "實名制",
    "本人帳號",
    "會員預售",
    "卡友優先",
]

# =========================================================
# TicketCat 共用品牌設定
# =========================================================

BRAND_NAME = "TicketCat"
BRAND_SLOGAN = "陪你追每一場演出"


# =========================================================
# 奶茶色系
# =========================================================

HEADER_COLOR = "#C9B29B"
URGENT_HEADER_COLOR = "#B56C55"

BODY_COLOR = "#FFFCF8"
CARD_COLOR = "#FFFFFF"
SECTION_COLOR = "#F4ECE4"

TEXT_COLOR = "#5C5148"
SUBTEXT_COLOR = "#75695F"
LIGHT_TEXT_COLOR = "#9A8D82"

LINE_COLOR = "#E7DDD2"
BUTTON_COLOR = "#B99F86"

WHITE_COLOR = "#FFFFFF"
HEADER_SUBTEXT_COLOR = "#FFF9F3"

TICKET_CARD_COLOR = "#FFF4D6"
PICKUP_CARD_COLOR = "#EEF3E8"
SHOW_CARD_COLOR = "#F8EAE4"

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
    安全處理 None、空字串與純空白。
    """

    if value is None:
        return default

    text = str(value).strip()

    return text if text else default


def remove_none_elements(value):
    """
    遞迴移除 Flex JSON 裡的 None。

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
    color=LINE_COLOR,
):
    """
    建立共用分隔線。
    """

    return {
        "type": "separator",
        "margin": margin,
        "color": color,
    }


# =========================================================
# TicketCat Logo
# =========================================================

def get_logo_url():
    """
    從 config 讀取公開 Logo 網址。

    網址不存在或不是 https 時，
    自動改用貓咪 Emoji。
    """

    logo_url = getattr(
        config,
        "DASHBOARD_LOGO_URL",
        "",
    )

    logo_url = str(
        logo_url or ""
    ).strip()

    if not logo_url.startswith("https://"):
        return None

    return logo_url


def build_logo_box(
    size=54,
):
    """
    建立圓形 TicketCat Logo。

    size 必須傳入整數，例如：
    54、60、66。
    """

    logo_url = get_logo_url()

    size_px = f"{size}px"
    radius_px = f"{size // 2}px"

    if not logo_url:

        return {
            "type": "box",
            "layout": "vertical",
            "width": size_px,
            "height": size_px,
            "backgroundColor": "#FFF7EC",
            "cornerRadius": radius_px,
            "justifyContent": "center",
            "alignItems": "center",
            "flex": 0,
            "contents": [
                {
                    "type": "text",
                    "text": "🐱",
                    "size": "xl",
                    "align": "center",
                }
            ],
        }

    return {
        "type": "box",
        "layout": "vertical",
        "width": size_px,
        "height": size_px,
        "cornerRadius": radius_px,
        "flex": 0,
        "contents": [
            {
                "type": "image",
                "url": logo_url,
                "size": "full",
                "aspectMode": "cover",
                "aspectRatio": "1:1",
            }
        ],
    }


# =========================================================
# TicketCat 品牌 Header
# =========================================================

def build_brand_header(
    subtitle=None,
    message=None,
    logo_size=44,
    urgent=False,
    show_logo=True,
    compact=True,
):
    """
    TicketCat 共用 Header。

    subtitle：
        品牌區下方的普通白字標題。

    message：
        米白色膠囊文字。

    urgent：
        True 時使用深紅棕色。

    compact：
        True 使用精簡高度。
    """

    brand_contents = []

    if show_logo:
        brand_contents.append(
            build_logo_box(
                size=logo_size
            )
        )

    brand_contents.append(
        {
            "type": "box",
            "layout": "vertical",
            "margin": (
                "md"
                if show_logo
                else "none"
            ),
            "flex": 1,
            "contents": [
                {
                    "type": "text",
                    "text": f"🐱 {BRAND_NAME}",
                    "size": "md",
                    "weight": "bold",
                    "color": WHITE_COLOR,
                    "wrap": True,
                },
                {
                    "type": "text",
                    "text": BRAND_SLOGAN,
                    "size": "xxs",
                    "color": HEADER_SUBTEXT_COLOR,
                    "margin": "xs",
                    "wrap": True,
                },
            ],
        }
    )

    contents = [
        {
            "type": "box",
            "layout": "horizontal",
            "alignItems": "center",
            "contents": brand_contents,
        }
    ]

    if subtitle:

        contents.append(
            {
                "type": "text",
                "text": safe_text(
                    subtitle,
                    "",
                ),
                "size": "xs",
                "weight": "bold",
                "color": WHITE_COLOR,
                "margin": "sm",
                "wrap": True,
            }
        )

    if message:

        contents.append(
            {
                "type": "box",
                "layout": "vertical",
                "margin": "sm",
                "backgroundColor": "#FFF7EC",
                "cornerRadius": "8px",
                "paddingTop": "6px",
                "paddingBottom": "6px",
                "paddingStart": "10px",
                "paddingEnd": "10px",
                "contents": [
                    {
                        "type": "text",
                        "text": safe_text(
                            message,
                            "",
                        ),
                        "size": "xxs",
                        "weight": "bold",
                        "color": TEXT_COLOR,
                        "align": "center",
                        "wrap": True,
                    }
                ],
            }
        )

    return {
        "type": "box",
        "layout": "vertical",
        "backgroundColor": (
            URGENT_HEADER_COLOR
            if urgent
            else HEADER_COLOR
        ),
        "paddingTop": (
            "11px"
            if compact
            else "14px"
        ),
        "paddingBottom": (
            "11px"
            if compact
            else "14px"
        ),
        "paddingStart": "16px",
        "paddingEnd": "16px",
        "contents": contents,
    }


# =========================================================
# TicketCat 品牌 Footer
# =========================================================

def build_brand_footer(
    margin="lg",
    show_separator=True,
):
    """
    建立共用品牌 Footer。
    """

    contents = []

    if show_separator:

        contents.append(
            {
                "type": "separator",
                "color": LINE_COLOR,
            }
        )

    contents.extend(
        [
            {
                "type": "text",
                "text": f"🐱 {BRAND_NAME}",
                "size": "xs",
                "weight": "bold",
                "color": LIGHT_TEXT_COLOR,
                "align": "center",
                "margin": "md",
                "wrap": False,
            },
            {
                "type": "text",
                "text": BRAND_SLOGAN,
                "size": "xxs",
                "color": LIGHT_TEXT_COLOR,
                "align": "center",
                "margin": "xs",
                "wrap": True,
            },
        ]
    )

    return {
        "type": "box",
        "layout": "vertical",
        "margin": margin,
        "paddingTop": "8px",
        "paddingBottom": "2px",
        "contents": contents,
    }


# =========================================================
# 共用狀態膠囊
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
        "cornerRadius": "10px",
        "paddingTop": "5px",
        "paddingBottom": "5px",
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


ACTIVITY_BADGE = {
    "演唱會": ("演唱會", "#E7D8C8"),      # 奶茶
    "FM": ("FAN MEETING", "#DCECF7"),    # 霧藍
    "FP": ("FAN PARTY", "#F8DDE7"),      # 淡粉
    "LIVE": ("LIVE", "#DDEEDC"),         # 淡綠
    "SHOWCASE": ("SHOWCASE", "#EEE3F7"), # 淡紫
    "拼盤": ("拼盤", "#F3E2D2"),          # 杏桃
    "FESTIVAL": ("FESTIVAL", "#F8E8C9"), # 淡金
    "其他": ("其他", "#EAEAEA"),          # 淺灰
}

# =========================================================
# Activity Options
# =========================================================

ACTIVITY_OPTIONS = [
    ("🎤 演唱會", "演唱會"),
    ("🤝 FAN MEETING", "FM"),
    ("🎉 FAN PARTY", "FP"),
    ("🎵 LIVE", "LIVE"),
    ("🌟 SHOWCASE", "SHOWCASE"),
    ("🎭 拼盤", "拼盤"),
    ("🎪 FESTIVAL", "FESTIVAL"),
    ("📌 其他", "其他"),
]


ACTIVITY_VALUES = {
    value
    for _, value in ACTIVITY_OPTIONS
}


def build_activity_badge(activity):

    text, color = ACTIVITY_BADGE.get(
        activity,
        ("其他", "#E5E5E5"),
    )

    return {
        "type": "box",
        "layout": "vertical",
        "backgroundColor": color,
        "cornerRadius": "999px",
        "paddingTop": "2px",
        "paddingBottom": "2px",
        "paddingStart": "7px",
        "paddingEnd": "7px",
        "flex": 0,
        "contents": [
            {
                "type": "text",
                "text": text,
                "size": "10px",
                "weight": "bold",
                "color": TEXT_COLOR,
                "align": "center",
                "wrap": False,
            }
        ],
    }

# =========================================================
# Activity Badge Row
# =========================================================

def build_activity_badge_row(
    activity,
    margin="none",
):

    return {
        "type": "box",
        "layout": "horizontal",
        "margin": margin,
        "contents": [
            build_activity_badge(activity)
        ],
    }


def build_waiting_tag(text):
    """
    黃色等待狀態。
    """

    return build_status_tag(
        text=text,
        background_color=WAITING_BACKGROUND_COLOR,
        text_color=WAITING_TEXT_COLOR,
    )


def build_success_tag(text):
    """
    綠色完成狀態。
    """

    return build_status_tag(
        text=text,
        background_color=SUCCESS_BACKGROUND_COLOR,
        text_color=SUCCESS_TEXT_COLOR,
    )


def build_failed_tag(text):
    """
    紅色失敗狀態。
    """

    return build_status_tag(
        text=text,
        background_color=FAILED_BACKGROUND_COLOR,
        text_color=FAILED_TEXT_COLOR,
    )


# =========================================================
# 共用奶茶按鈕
# =========================================================

def build_milk_tea_button(
    label,
    action_text,
    flex=1,
    text_size="xs",
):
    """
    建立可調整字體大小的奶茶色圓角按鈕。
    """

    return {
        "type": "box",
        "layout": "vertical",
        "flex": flex,
        "backgroundColor": BUTTON_COLOR,
        "cornerRadius": "10px",
        "paddingTop": "10px",
        "paddingBottom": "10px",
        "paddingStart": "4px",
        "paddingEnd": "4px",
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
                "size": text_size,
                "weight": "bold",
                "color": WHITE_COLOR,
                "align": "center",
                "wrap": False,
            }
        ],
    }