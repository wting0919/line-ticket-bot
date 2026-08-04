from theme import (
    CARD_COLOR,
    SECTION_COLOR,
    TICKET_CARD_COLOR,
    PICKUP_CARD_COLOR,
    SHOW_CARD_COLOR,
    TEXT_COLOR,
    SUBTEXT_COLOR,
    LINE_COLOR,
)


# =========================================================
# 今日待辦問候語
# =========================================================

def get_today_cat_message(
    ticket_count,
    pickup_count,
    show_count,
):
    """
    依照今日待辦內容，產生單行 TicketCat 問候語。
    """

    total_count = (
        ticket_count
        + pickup_count
        + show_count
    )

    active_types = sum([
        ticket_count > 0,
        pickup_count > 0,
        show_count > 0,
    ])

    if total_count == 0:
        return "🐱 今天沒有待辦，好好休息吧 ☕"

    if active_types >= 2:
        return "🐱 今天很忙喔，我陪你一起完成 💪"

    if show_count > 0:
        return "🐱 今天就是演出日，玩得開心 ✨"

    if ticket_count > 0:
        return "🐱 今天要搶票，祝你順利搶到 🎟"

    if pickup_count > 0:
        return "🐱 記得去取票喔，不要白跑一趟 📦"

    return "🐱 今天有待辦，記得查看一下～"


def build_today_cat_message(
    ticket_count,
    pickup_count,
    show_count,
):
    """
    建立單行 TicketCat 問候區。
    """

    message = get_today_cat_message(
        ticket_count=ticket_count,
        pickup_count=pickup_count,
        show_count=show_count,
    )

    return {
        "type": "box",
        "layout": "vertical",
        "margin": "sm",
        "paddingTop": "7px",
        "paddingBottom": "7px",
        "paddingStart": "9px",
        "paddingEnd": "9px",
        "backgroundColor": SECTION_COLOR,
        "cornerRadius": "9px",
        "contents": [
            {
                "type": "text",
                "text": message,
                "size": "xxs",
                "weight": "bold",
                "color": TEXT_COLOR,
                "wrap": True,
            }
        ],
    }


# =========================================================
# 今日待辦摘要格
# =========================================================

def build_summary_card(
    icon,
    label,
    count,
    background_color,
    action_text,
):
    """
    建立精簡版可點擊摘要格。
    """

    return {
        "type": "box",
        "layout": "horizontal",
        "flex": 1,
        "backgroundColor": background_color,
        "cornerRadius": "11px",
        "paddingTop": "6px",
        "paddingBottom": "6px",
        "paddingStart": "7px",
        "paddingEnd": "7px",
        "alignItems": "center",
        "action": {
            "type": "message",
            "label": label,
            "text": action_text,
        },
        "contents": [
            {
                "type": "text",
                "text": icon,
                "size": "lg",
                "flex": 0,
            },
            {
                "type": "box",
                "layout": "vertical",
                "margin": "sm",
                "flex": 1,
                "contents": [
                    {
                        "type": "text",
                        "text": str(count),
                        "size": "lg",
                        "weight": "bold",
                        "color": TEXT_COLOR,
                        "align": "center",
                    },
                    {
                        "type": "text",
                        "text": label,
                        "size": "xxs",
                        "color": SUBTEXT_COLOR,
                        "align": "center",
                        "margin": "xs",
                        "wrap": False,
                    },
                ],
            },
        ],
    }


# =========================================================
# 共用今日待辦
# =========================================================

def build_today_summary(
    ticket_count,
    pickup_count,
    show_count,
    date_text=None,
):
    """
    Dashboard 與 Today Card 共用的今日待辦區塊。

    摘要入口：
    🎟 待搶票 → 搶票列表
    📦 待取票 → 取票列表
    📋 演出表 → 演出列表
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
        "cornerRadius": "14px",
        "paddingTop": "10px",
        "paddingBottom": "10px",
        "paddingStart": "10px",
        "paddingEnd": "10px",
        "borderWidth": "1px",
        "borderColor": LINE_COLOR,
        "contents": [
            {
                "type": "box",
                "layout": "vertical",
                "action": {
                    "type": "message",
                    "label": "今日待辦",
                    "text": "今日待辦",
                },
                "contents": [
                    {
                        "type": "text",
                        "text": "☀️ 今日待辦",
                        "size": "md",
                        "weight": "bold",
                        "color": TEXT_COLOR,
                        "wrap": True,
                    },
                    *(
                        [{
                            "type": "box",
                            "layout": "horizontal",
                            "margin": "xs",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": date_text,
                                    "size": "xxs",
                                    "color": SUBTEXT_COLOR,
                                    "flex": 1,
                                    "wrap": True,
                                },
                                {
                                    "type": "text",
                                    "text": f"共 {total_count} 項",
                                    "size": "xxs",
                                    "color": SUBTEXT_COLOR,
                                    "align": "end",
                                    "flex": 0,
                                    "wrap": False,
                                },
                            ],
                        }] if date_text else [{
                            "type": "text",
                            "text": f"共 {total_count} 項",
                            "size": "xxs",
                            "color": SUBTEXT_COLOR,
                            "align": "end",
                        }]
                    ),
                ],
            },
            {
                "type": "box",
                "layout": "horizontal",
                "spacing": "xs",
                "margin": "md",
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
                        icon="📋",
                        label="演出表",
                        count=show_count,
                        background_color=SHOW_CARD_COLOR,
                        action_text="演出列表",
                    ),
                ],
            },
            build_today_cat_message(
                ticket_count=ticket_count,
                pickup_count=pickup_count,
                show_count=show_count,
            ),
        ],
    }