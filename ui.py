from data import load_members

from linebot.models import (
    TextSendMessage,
    QuickReply,
    QuickReplyButton,
    MessageAction,
)

# =====================
# 查看列表 Quick Reply
# =====================

def view_list_quick_reply(count):

    items = []

    for i in range(1, min(count, 9) + 1):

        items.append(
            QuickReplyButton(
                action=MessageAction(
                    label=f"👀 {i}",
                    text=f"查看 {i}"
                )
            )
        )

    return QuickReply(items=items)


# =====================
# 共用列表回覆
# =====================

def list_reply(reply, count):

    return TextSendMessage(
        text=reply,
        quick_reply=view_list_quick_reply(count)
    )


def menu_reply(text):

    return TextSendMessage(
        text=text,
        quick_reply=QuickReply(
            items=[
                
                QuickReplyButton(
                    action=MessageAction(
                        label="➕ 新增演出",
                        text="新增演出"
                    )
                ),

                QuickReplyButton(
                    action=MessageAction(
                        label="🎟 搶票列表",
                        text="搶票列表"
                    )
                ),

                QuickReplyButton(
                    action=MessageAction(
                        label="🎫 取票列表",
                        text="取票列表"
                    )
                ),

                QuickReplyButton(
                    action=MessageAction(
                        label="📅 演出列表",
                        text="演出列表"
                    )
                ),

                QuickReplyButton(
                    action=MessageAction(
                        label="❓ 幫助",
                        text="幫助"
                    )
                ),


            ]
        )
    )

def member_quick_reply(
    selected=None,
    allow_finish=False,
    allow_skip=True
):

    selected = selected or []

    members = load_members()

    items = []

    for name in members:

        if name in selected:
            continue

        items.append(
            QuickReplyButton(
                action=MessageAction(
                    label=f"👤 {name}",
                    text=name
                )
            )
        )

    if allow_finish:

        items.append(
            QuickReplyButton(
                action=MessageAction(
                    label="✅ 完成",
                    text="完成"
                )
            )
        )

    if allow_skip:

        items.append(
            QuickReplyButton(
                action=MessageAction(
                    label="➖ 略過",
                    text="略過"
                )
            )
        )

    items.append(
        QuickReplyButton(
            action=MessageAction(
                label="❌ 取消",
                text="取消"
            )
        )
    )

    return QuickReply(items=items)


def simple_quick_reply(buttons):

    items = []

    for label, value in buttons:

        items.append(
            QuickReplyButton(
                action=MessageAction(
                    label=label,
                    text=value
                )
            )
        )

    return QuickReply(items=items)


def edit_field_quick_reply():

    return simple_quick_reply([
        ("🎤 藝人", "藝人"),
        ("🏷 活動", "活動"),
        ("✨ 活動名稱", "活動名稱"),
        ("📅 演出日期", "演出日期"),
        ("🕒 搶票時間", "搶票時間"),
        ("🌐 售票平台", "售票平台"),
        ("💰 價格張數", "價格張數"),
        ("🪪 會員資訊", "會員資訊"),
        ("🔔 提醒事項", "提醒事項"),
        ("📦 取票日期", "取票日期"),
        ("📝 備註", "備註"),
        ("❌ 取消", "取消")
    ])
