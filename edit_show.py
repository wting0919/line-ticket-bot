from linebot.models import TextSendMessage

from data import (
    load_data,
    update_show,
)

from utils import (
    normalize_show_date,
    normalize_ticket_time,
    normalize_pickup_date,
    format_show_dates,
)

from ui import (
    simple_quick_reply,
    edit_field_quick_reply,
)

from show_list import (
    get_all_shows,
)

from helpers import (
    get_state,
    set_state,
    clear_state,
)

from theme import (
    activity_quick_reply,
    reminder_quick_reply,
    reminder_message,
    ACTIVITY_VALUES,
    REMINDER_OPTIONS,
)

import config


ALLOWED_FIELDS = {
    "藝人",
    "活動",
    "活動名稱",
    "演出日期",
    "搶票時間",
    "價格張數",
    "售票平台",
    "售票網址",
    "會員資訊",
    "注意事項",
    "售票階段",
    "取票日期",
    "備註",
}


FIELD_HINTS = {
    "藝人": "請輸入新的藝人",
    "活動": "請選擇新的活動類型",
    "活動名稱": "請輸入新的活動名稱",
    "演出日期": "請輸入新的演出日期\n例如：10/1",
    "搶票時間": "請輸入新的搶票時間\n例如：9/1 12:00",
    "價格張數": "請輸入新的價格張數\n例如：3800*2",
    "售票平台": "請輸入新的售票平台",
    "售票網址": "請輸入新的售票網址\n例如：https://tixcraft.com/",
    "會員資訊": "請輸入新的會員資訊\n也可按「清除」",
    "注意事項": "請選擇新的注意事項",
    "售票階段": "請選擇新的售票階段",
    "取票日期": "請輸入新的取票日期\n例如：5天前、9/25\n也可按「清除」",
    "備註": "請輸入新的備註\n也可按「清除」",
}


# =========================================================
# 共用：取得演出
# =========================================================

def get_show_by_id(show_id):

    return next(
        (
            item
            for item in load_data()
            if item.get("id") == show_id
        ),
        None,
    )


# =========================================================
# 共用：建立修改欄位選單
# =========================================================

def show_edit_menu(event, user_id, message=None):

    state = get_state(user_id)

    if not isinstance(state, dict):
        return False

    page = state.get(
        "field_page",
        1
    )

    if message is None:
        message = "✏️ 請選擇要修改的欄位"

    config.line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=message,
            quick_reply=edit_field_quick_reply(page)
        )
    )

    return True


# =========================================================
# 開始修改演出
# =========================================================

def start_edit_show(event, text, user_id):

    state = get_state(user_id)

    if (
        isinstance(state, dict)
        and "shows" in state
    ):
        shows = state["shows"]

    else:
        shows = get_all_shows()

    try:

        show_id = int(
            text.replace(
                "修改ID",
                ""
            ).strip()
        )

    except ValueError:

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="請輸入格式：\n修改ID 5"
            )
        )

        return True

    show = next(
        (
            item
            for item in shows
            if item.get("id") == show_id
        ),
        None,
    )

    if show is None:

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="❌ 找不到這筆演出"
            )
        )

        return True

    set_state(
        user_id,
        {
            "mode": "修改演出",
            "step": "field",
            "show_id": show["id"],
            "field_page": 1,
        }
    )

    message = (
        "✏️ 修改演出\n\n"
        f"🎤 {show.get('藝人', '')}\n"
        f"🏷️ {show.get('活動', '')}\n"
    )

    if show.get("活動名稱"):

        message += (
            f"✨ {show.get('活動名稱')}\n"
        )

    message += (
        "\n請選擇要修改的欄位\n"
        "修改完成後可繼續選其他欄位"
    )

    config.line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=message,
            quick_reply=edit_field_quick_reply(1)
        )
    )

    return True


# =========================================================
# 修改成功後
# 不離開修改模式
# =========================================================

def edit_success_menu(
    event,
    user_id,
    show,
    field,
    old_value,
    new_value,
):

    if field == "演出日期":

        old_display = (
            format_show_dates(old_value)
            if old_value
            else "無"
        )

        new_display = (
            format_show_dates(new_value)
            if new_value
            else "無"
        )

    else:

        old_display = (
            old_value
            if old_value
            else "無"
        )

        new_display = (
            new_value
            if new_value
            else "無"
        )

    message = (
        "✅ 修改成功\n"
        "──────────\n"
        f"🎤 {show.get('藝人', '')}\n"
        f"🏷️ {show.get('活動', '')}\n"
    )

    if show.get("活動名稱"):

        message += (
            f"✨ {show['活動名稱']}\n"
        )

    message += (
        "──────────\n"
        f"✏️ {field}\n"
        f"🔸 原本：{old_display}\n"
        f"🔹 修改後：{new_display}\n"
        "──────────\n"
        "還可以繼續修改其他欄位"
    )

    show_edit_menu(
        event,
        user_id,
        message
    )

    return True


# =========================================================
# 修改演出主流程
# =========================================================

def handle_edit_show_flow(
    event,
    text,
    user_id
):

    state = get_state(user_id)

    if (
        not isinstance(state, dict)
        or state.get("mode") != "修改演出"
    ):

        return False

    step = state.get("step")

    # =====================================================
    # 自訂注意事項時的取消
    # 只回到注意事項選單
    # =====================================================

    if (
        text == "取消"
        and step == "custom_reminder"
    ):

        state["step"] = "reminder"

        set_state(
            user_id,
            state
        )

        selected = state.setdefault(
            "selected_reminders",
            []
        )

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=reminder_message(
                    selected
                ),
                quick_reply=reminder_quick_reply()
            )
        )

        return True

    # =====================================================
    # 一般取消
    # =====================================================

    if text == "取消":

        clear_state(
            user_id
        )

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="已取消修改演出"
            )
        )

        return True

    # =====================================================
    # FIELD：選擇欄位
    # =====================================================

    if step == "field":

        # -------------------------------------------------
        # 完成修改
        # -------------------------------------------------

        if text == "完成修改":

            show = get_show_by_id(
                state["show_id"]
            )

            clear_state(
                user_id
            )

            if show:

                config.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text=(
                            "✅ 修改完成\n"
                            "──────────\n"
                            f"🎤 {show.get('藝人', '')}\n"
                            f"🏷️ {show.get('活動', '')}\n"
                            + (
                                f"✨ {show.get('活動名稱')}\n"
                                if show.get("活動名稱")
                                else ""
                            )
                            + "已離開修改模式"
                        )
                    )
                )

            else:

                config.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="✅ 修改完成"
                    )
                )

            return True

        # -------------------------------------------------
        # 下一頁
        # -------------------------------------------------

        if text == "修改下一頁":

            state["field_page"] = 2

            set_state(
                user_id,
                state
            )

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="✏️ 請選擇要修改的欄位",
                    quick_reply=edit_field_quick_reply(2)
                )
            )

            return True

        # -------------------------------------------------
        # 上一頁
        # -------------------------------------------------

        if text == "修改上一頁":

            state["field_page"] = 1

            set_state(
                user_id,
                state
            )

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="✏️ 請選擇要修改的欄位",
                    quick_reply=edit_field_quick_reply(1)
                )
            )

            return True

        # -------------------------------------------------
        # 不認識的欄位
        # -------------------------------------------------

        if text not in ALLOWED_FIELDS:

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="請使用下方按鈕選擇欄位",
                    quick_reply=edit_field_quick_reply(
                        state.get(
                            "field_page",
                            1
                        )
                    )
                )
            )

            return True

        # =================================================
        # 活動
        # =================================================

        if text == "活動":

            state["field"] = "活動"
            state["step"] = "activity"

            set_state(
                user_id,
                state
            )

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="🏷 請選擇活動類型",
                    quick_reply=activity_quick_reply()
                )
            )

            return True

        # =================================================
        # 售票階段
        # =================================================

        if text == "售票階段":

            state["field"] = "售票階段"
            state["step"] = "sale_stage"

            set_state(
                user_id,
                state
            )

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="🚩 請選擇新的售票階段",
                    quick_reply=simple_quick_reply([
                        ("會員預售", "會員預售"),
                        ("卡友優先", "卡友優先"),
                        ("公售", "公售"),
                        ("❌ 取消", "取消"),
                    ])
                )
            )

            return True

        # =================================================
        # 注意事項
        # =================================================

        if text == "注意事項":

            state["field"] = "注意事項"
            state["step"] = "reminder"

            show = get_show_by_id(
                state["show_id"]
            )

            if show is None:

                clear_state(
                    user_id
                )

                config.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="❌ 找不到這筆演出"
                    )
                )

                return True

            state["selected_reminders"] = (
                show.get(
                    "注意事項",
                    ""
                ).splitlines()
                if show.get("注意事項")
                else []
            )

            set_state(
                user_id,
                state
            )

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=reminder_message(
                        state["selected_reminders"]
                    ),
                    quick_reply=reminder_quick_reply()
                )
            )

            return True

        # =================================================
        # 一般文字欄位
        # =================================================

        state["field"] = text
        state["step"] = "value"

        buttons = []

        if text in {
            "會員資訊",
            "售票網址",
            "取票日期",
            "備註",
        }:

            buttons.append(
                ("🗑 清除", "清除")
            )

        buttons.append(
            ("❌ 取消", "取消")
        )

        set_state(
            user_id,
            state
        )

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=FIELD_HINTS[text],
                quick_reply=simple_quick_reply(
                    buttons
                )
            )
        )

        return True

    # =====================================================
    # 活動
    # =====================================================

    if step == "activity":

        if text not in ACTIVITY_VALUES:

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="請使用下方按鈕選擇活動類型",
                    quick_reply=activity_quick_reply()
                )
            )

            return True

        show = get_show_by_id(
            state["show_id"]
        )

        if show is None:

            clear_state(
                user_id
            )

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="❌ 找不到這筆演出"
                )
            )

            return True

        old_value = (
            show.get("活動")
            or "其他"
        )

        show["活動"] = text

        try:

            update_show(show)

        except Exception as e:

            print(
                "修改活動失敗：",
                repr(e),
                flush=True
            )

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"❌ 修改失敗\n{e}"
                )
            )

            return True

        state["step"] = "field"
        state.pop("field", None)

        set_state(
            user_id,
            state
        )

        return edit_success_menu(
            event,
            user_id,
            show,
            "活動",
            old_value,
            text
        )

    # =====================================================
    # 售票階段
    # =====================================================

    if step == "sale_stage":

        if text not in [
            "會員預售",
            "卡友優先",
            "公售",
        ]:

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="請使用下方按鈕選擇售票階段",
                    quick_reply=simple_quick_reply([
                        ("會員預售", "會員預售"),
                        ("卡友優先", "卡友優先"),
                        ("公售", "公售"),
                        ("❌ 取消", "取消"),
                    ])
                )
            )

            return True

        show = get_show_by_id(
            state["show_id"]
        )

        if show is None:

            clear_state(
                user_id
            )

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="❌ 找不到這筆演出"
                )
            )

            return True

        old_value = (
            show.get("售票階段")
            or ""
        )

        show["售票階段"] = text

        try:

            update_show(show)

        except Exception as e:

            print(
                "修改售票階段失敗：",
                repr(e),
                flush=True
            )

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"❌ 修改失敗\n{e}"
                )
            )

            return True

        state["step"] = "field"
        state.pop("field", None)

        set_state(
            user_id,
            state
        )

        return edit_success_menu(
            event,
            user_id,
            show,
            "售票階段",
            old_value,
            text
        )

    # =====================================================
    # 注意事項
    # =====================================================

    if step == "reminder":

        selected = state.setdefault(
            "selected_reminders",
            []
        )

        # -------------------------------------------------
        # 略過
        # -------------------------------------------------

        if text == "略過":

            show = get_show_by_id(
                state["show_id"]
            )

            if show is None:

                clear_state(
                    user_id
                )

                config.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="❌ 找不到這筆演出"
                    )
                )

                return True

            old_value = (
                show.get("注意事項")
                or ""
            )

            show["注意事項"] = ""

            try:

                update_show(show)

            except Exception as e:

                print(
                    "修改注意事項失敗：",
                    repr(e),
                    flush=True
                )

                config.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text=f"❌ 修改失敗\n{e}"
                    )
                )

                return True

            state["step"] = "field"
            state.pop(
                "selected_reminders",
                None
            )

            set_state(
                user_id,
                state
            )

            return edit_success_menu(
                event,
                user_id,
                show,
                "注意事項",
                old_value,
                ""
            )

        # -------------------------------------------------
        # 完成
        # -------------------------------------------------

        if text == "完成":

            if not selected:

                config.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="請至少選擇一項，或按「略過」",
                        quick_reply=reminder_quick_reply()
                    )
                )

                return True

            show = get_show_by_id(
                state["show_id"]
            )

            if show is None:

                clear_state(
                    user_id
                )

                config.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="❌ 找不到這筆演出"
                    )
                )

                return True

            old_value = (
                show.get("注意事項")
                or ""
            )

            new_value = "\n".join(
                selected
            )

            show["注意事項"] = new_value

            try:

                update_show(show)

            except Exception as e:

                print(
                    "修改注意事項失敗：",
                    repr(e),
                    flush=True
                )

                config.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text=f"❌ 修改失敗\n{e}"
                    )
                )

                return True

            state["step"] = "field"
            state.pop(
                "selected_reminders",
                None
            )

            set_state(
                user_id,
                state
            )

            return edit_success_menu(
                event,
                user_id,
                show,
                "注意事項",
                old_value,
                new_value
            )

        # -------------------------------------------------
        # 自訂
        # -------------------------------------------------

        if text in {
            "自訂",
            "自訂提醒",
        }:

            state["step"] = "custom_reminder"

            set_state(
                user_id,
                state
            )

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=(
                        "✏️ 請輸入注意事項\n\n"
                        "輸入完成後會回到注意事項選單"
                    ),
                    quick_reply=simple_quick_reply([
                        ("❌ 取消", "取消")
                    ])
                )
            )

            return True

        # -------------------------------------------------
        # 預設注意事項
        # -------------------------------------------------

        if text in REMINDER_OPTIONS:

            if text not in selected:

                selected.append(
                    text
                )

            set_state(
                user_id,
                state
            )

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=reminder_message(
                        selected
                    ),
                    quick_reply=reminder_quick_reply()
                )
            )

            return True

        # -------------------------------------------------
        # 不認識
        # -------------------------------------------------

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="請使用下方按鈕選擇注意事項",
                quick_reply=reminder_quick_reply()
            )
        )

        return True

    # =====================================================
    # 自訂注意事項
    # =====================================================

    if step == "custom_reminder":

        text = text.strip()

        if not text:

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=(
                        "❌ 注意事項不可空白\n\n"
                        "請重新輸入，或按「取消」"
                    ),
                    quick_reply=simple_quick_reply([
                        ("❌ 取消", "取消")
                    ])
                )
            )

            return True

        selected = state.setdefault(
            "selected_reminders",
            []
        )

        if text not in selected:

            selected.append(
                text
            )

        state["step"] = "reminder"

        set_state(
            user_id,
            state
        )

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=reminder_message(
                    selected
                ),
                quick_reply=reminder_quick_reply()
            )
        )

        return True

    # =====================================================
    # 一般欄位
    # =====================================================

    if step == "value":

        field = state.get(
            "field"
        )

        show = get_show_by_id(
            state["show_id"]
        )

        if show is None:

            clear_state(
                user_id
            )

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="❌ 找不到這筆演出，請重新操作"
                )
            )

            return True

        try:

            # -------------------------------------------------
            # 演出日期
            # -------------------------------------------------

            if field == "演出日期":

                new_value = normalize_show_date(
                    text
                )

            # -------------------------------------------------
            # 搶票時間
            # -------------------------------------------------

            elif field == "搶票時間":

                new_value = normalize_ticket_time(
                    text
                )

            # -------------------------------------------------
            # 取票日期
            # -------------------------------------------------

            elif field == "取票日期":

                if text == "清除":

                    new_value = ""

                else:

                    new_value = normalize_pickup_date(
                        text,
                        show.get(
                            "演出日期",
                            ""
                        )
                    )

            # -------------------------------------------------
            # 可清除文字欄位
            # -------------------------------------------------

            elif field in {
                "會員資訊",
                "售票網址",
                "備註",
            }:

                if text == "清除":

                    new_value = ""

                else:

                    new_value = text.strip()

            # -------------------------------------------------
            # 其他
            # -------------------------------------------------

            else:

                new_value = text.strip()

        except ValueError:

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=(
                        "❌ 格式不正確，請重新輸入\n\n"
                        "輸入「取消」可回到修改欄位"
                    )
                )
            )

            return True

        except Exception as e:

            print(
                "修改演出失敗：",
                repr(e),
                flush=True
            )

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"❌ 修改失敗\n{e}"
                )
            )

            return True

        # -------------------------------------------------
        # 記錄原值
        # -------------------------------------------------

        old_value = (
            show.get(field)
            or ""
        )

        # -------------------------------------------------
        # 寫入新值
        # -------------------------------------------------

        show[field] = new_value

        # -------------------------------------------------
        # 修改日期／搶票時間後
        # 相關提醒重新計算
        # -------------------------------------------------

        if field in {
            "演出日期",
            "搶票時間",
        }:

            show.setdefault(
                "提醒",
                {}
            )

            show["提醒"]["前一天"] = False
            show["提醒"]["30分鐘"] = False
            show["提醒"]["10分鐘"] = False

        # -------------------------------------------------
        # 修改演出日期
        # 演出日提醒、取票提醒也要重置
        # -------------------------------------------------

        if field == "演出日期":

            show.setdefault(
                "提醒",
                {}
            )

            show["提醒"]["演出日"] = False

            if show.get("取票日期"):

                show["提醒"]["取票"] = False

        # -------------------------------------------------
        # 寫入資料庫
        # -------------------------------------------------

        try:

            update_show(
                show
            )

        except Exception as e:

            print(
                "更新資料庫失敗：",
                repr(e),
                flush=True
            )

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=(
                        "❌ 修改失敗\n\n"
                        f"{e}\n\n"
                        "資料沒有成功更新，"
                        "你可以繼續重新輸入。"
                    )
                )
            )

            return True

        # -------------------------------------------------
        # 修改成功
        #
        # ★ 不 clear_state
        # ★ 回到 field
        # -------------------------------------------------

        state["step"] = "field"
        state.pop(
            "field",
            None
        )

        set_state(
            user_id,
            state
        )

        return edit_success_menu(
            event,
            user_id,
            show,
            field,
            old_value,
            new_value
        )

    # =====================================================
    # 未知狀態
    # 不要直接清掉
    # =====================================================

    print(
        "⚠️ 修改流程狀態異常：",
        "step =", repr(step),
        "text =", repr(text),
        "state =", repr(state),
        flush=True
    )

    set_state(
        user_id,
        state
    )

    config.line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=(
                "⚠️ 目前修改流程仍然保留。\n\n"
                "請繼續操作，或按「取消」結束。"
            ),
            quick_reply=edit_field_quick_reply(
                state.get(
                    "field_page",
                    1
                )
            )
        )
    )

    return True
