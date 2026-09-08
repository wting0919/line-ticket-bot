from copy import deepcopy

from linebot.models import TextSendMessage

from data import (
    insert_show,
)

from show_list import (
    get_all_shows,
)

from ui import (
    edit_field_quick_reply,
)

from helpers import (
    get_state,
    set_state,
)

import config


# =========================================================
# 複製演出
# =========================================================

def handle_copy_show(event, text, user_id):

    state = get_state(user_id)

    # -----------------------------------------------------
    # 優先使用目前列表
    # -----------------------------------------------------

    if isinstance(state, dict) and "shows" in state:

        shows = state["shows"]

    else:

        shows = get_all_shows()

    # -----------------------------------------------------
    # 解析複製 ID
    # -----------------------------------------------------

    try:

        show_id = int(
            text.replace("複製ID", "").strip()
        )

    except ValueError:

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="請輸入格式：\n複製ID 1"
            )
        )

        return True

    # -----------------------------------------------------
    # 找原演出
    # -----------------------------------------------------

    source_show = next(
        (
            item
            for item in shows
            if item.get("id") == show_id
        ),
        None,
    )

    if source_show is None:

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="❌ 找不到這筆演出"
            )
        )

        return True

    # -----------------------------------------------------
    # 複製資料
    # -----------------------------------------------------

    new_show = deepcopy(
        source_show
    )

    # -----------------------------------------------------
    # 移除資料庫自動產生欄位
    # -----------------------------------------------------

    new_show.pop(
        "id",
        None
    )

    new_show.pop(
        "created_at",
        None
    )

    new_show.pop(
        "updated_at",
        None
    )

    # =====================================================
    # 重置複製後的狀態
    # =====================================================

    new_show["提醒"] = {
        "前一天": False,
        "30分鐘": False,
        "10分鐘": False,
        "取票": False,
        "演出日": False,
    }

    new_show["搶票狀態"] = "待搶票"
    new_show["取票狀態"] = "未取票"

    new_show["搶票大師"] = ""
    new_show["取票人"] = ""

    # -----------------------------------------------------
    # 搶票時間
    #
    # ★ timestamp 欄位不能放 ""
    # ★ 要用 None → PostgreSQL NULL
    # -----------------------------------------------------

    new_show["搶票時間"] = None

    # -----------------------------------------------------
    # 售票階段是文字欄位，所以可以使用 ""
    # -----------------------------------------------------

    new_show["售票階段"] = ""

    # -----------------------------------------------------
    # 如果取票日期本身是空字串
    # timestamp 欄位也要轉成 None
    # -----------------------------------------------------

    if (
        "取票日期" in new_show
        and new_show["取票日期"] == ""
    ):

        new_show["取票日期"] = None

    # =====================================================
    # 寫入資料庫
    # =====================================================

    try:

        inserted_show = insert_show(
            new_show
        )

    except Exception as e:

        print(
            "複製演出失敗：",
            repr(e),
            flush=True
        )

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=(
                    "❌ 複製失敗\n\n"
                    f"{e}\n\n"
                    "原演出沒有受到影響。"
                )
            )
        )

        return True

    # -----------------------------------------------------
    # insert_show 沒有回傳資料
    # -----------------------------------------------------

    if not isinstance(
        inserted_show,
        dict
    ):

        print(
            "⚠️ 複製成功但 insert_show 沒有回傳資料：",
            repr(inserted_show),
            flush=True
        )

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=(
                    "⚠️ 演出可能已建立，"
                    "但無法取得新演出的 ID。\n\n"
                    "請重新整理演出列表確認。"
                )
            )
        )

        return True

    new_show = inserted_show

    # =====================================================
    # 進入修改模式
    # =====================================================

    set_state(
        user_id,
        {
            "mode": "修改演出",
            "step": "field",
            "show_id": new_show.get("id"),
        }
    )

    # =====================================================
    # 顯示複製結果
    # =====================================================

    message = (
        "✅ 已建立複製演出\n"
        "──────────\n"
        f"🎤 {new_show.get('藝人', '')}\n"
        f"🏷️ {new_show.get('活動', '')}\n"
    )

    if new_show.get("活動名稱"):

        message += (
            f"✨ {new_show['活動名稱']}\n"
        )

    message += (
        "──────────\n"
        "已清除：\n"
        "🕒 搶票時間\n"
        "🚩 售票階段\n\n"
        "請選擇要修改的欄位"
    )        )

    except ValueError:

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="請輸入格式：\n複製ID 1"
            )
        )
        return True

    source_show = next(
        (
            item
            for item in shows
            if item.get("id") == show_id
        ),
        None,
    )

    if source_show is None:

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="❌ 找不到這筆演出"
            )
        )

        return True

    new_show = deepcopy(source_show)

    new_show.pop("id", None)
    new_show.pop("created_at", None)
    new_show.pop("updated_at", None)

    new_show["提醒"] = {
        "前一天": False,
        "30分鐘": False,
        "10分鐘": False,
        "取票": False,
        "演出日": False,
    }

    new_show["搶票狀態"] = "待搶票"
    new_show["取票狀態"] = "未取票"

    new_show["搶票時間"] = ""
    new_show["售票階段"] = ""

    new_show["搶票大師"] = ""
    new_show["取票人"] = ""


    try:
        new_show = insert_show(new_show)

    except Exception as e:

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=f"❌ 複製失敗\n{e}"
            )
        )
        return True

    set_state(
        user_id,
        {
            "mode": "修改演出",
            "step": "field",
            "show_id": new_show.get("id"),
        }
    )

    message = (
        "✅ 已建立複製演出\n"
        "──────────\n"
        f"🎤 {new_show.get('藝人', '')}\n"
        f"🏷️ {new_show.get('活動', '')}\n"
    )

    if new_show.get("活動名稱"):
        message += f"✨ {new_show['活動名稱']}\n"

    message += (
        "──────────\n"
        "已清除：🕒 搶票時間、🚩 售票階段\n"
        "請選擇要修改的欄位"
    )

    config.line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=message,
            quick_reply=edit_field_quick_reply()
        )
    )

    return True
