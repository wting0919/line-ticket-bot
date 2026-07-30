CHANNEL_ACCESS_TOKEN = None

import requests

from data import (
    get_member_user_id,
)


def push_mention_message(to, message_text, names):
    """使用 LINE textV2 傳送真正的 @ 提及。

    找不到 members.user_id 的名字會保留為普通文字，
    讓整則提醒不會因單一成員資料缺漏而失敗。
    """

    names = [
        str(name).strip()
        for name in (names or [])
        if str(name).strip()
    ]

    substitution = {}
    mention_lines = []
    missing_names = []

    # LINE 單則訊息最多可替換 20 個 mention。
    for index, name in enumerate(names[:20]):
        user_id = get_member_user_id(name)

        if user_id:
            key = f"mention{index}"
            mention_lines.append(f"{{{key}}}")
            substitution[key] = {
                "type": "mention",
                "mentionee": {
                    "type": "user",
                    "userId": user_id
                }
            }
        else:
            mention_lines.append(f"@{name}")
            missing_names.append(name)

    final_text = message_text

    if mention_lines:
        final_text += "\n\n" + "\n".join(mention_lines)

    payload = {
        "to": to,
        "messages": [
            {
                "type": "textV2",
                "text": final_text,
                "substitution": substitution
            }
        ]
    }

    # 沒有真正 mention 時，substitution 不需要送出。
    if not substitution:
        payload["messages"][0].pop("substitution", None)

    response = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers={
            "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=15
    )

    if not response.ok:
        raise RuntimeError(
            f"LINE mention 發送失敗：{response.status_code} {response.text}"
        )

    if missing_names:
        print("以下成員找不到 user_id，改用普通文字：", missing_names)

    return True
