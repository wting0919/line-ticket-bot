from linebot.models import (
    TextSendMessage,
    QuickReply,
    QuickReplyButton,
    MessageAction,
)

from data import load_members


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

    print(
        "Quick Reply 讀到的成員：",
        members,
        flush=True
    )

    items = []

    for name in members.keys():

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
        ("🎤 演出名稱", "演出名稱"),
        ("📅 演出日期", "演出日期"),
        ("🎟 搶票時間", "搶票時間"),
        ("💰 價格張數", "價格張數"),
        ("🌐 售票平台", "售票平台"),
        ("🎫 取票日期", "取票日期"),
        ("📝 備註", "備註"),
        ("❌ 取消", "取消")
    ])

