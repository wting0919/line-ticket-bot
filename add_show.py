import config

from linebot.models import TextSendMessage

from data import (
    insert_show,
)

from utils import (
    normalize_show_date,
    normalize_ticket_time,
    normalize_pickup_date,
    format_show_dates,
    format_datetime,
)

from ui import (
    simple_quick_reply,
)

from theme import (
    activity_quick_reply,
    ACTIVITY_VALUES,
    reminder_message,
    reminder_quick_reply,
    REMINDER_OPTIONS,
)

from helpers import (
    get_state,
    set_state,
    clear_state,
)


# =========================================================
# 共用：安全回覆
# =========================================================

def reply_message(event, message):

    try:

        config.line_bot_api.reply_message(
            event.reply_token,
            message
        )

        return True

    except Exception as e:

        print(
            "LINE 回覆失敗：",
            repr(e),
            flush=True
        )

        return False


# =========================================================
# 開始新增演出
# =========================================================

def start_add_show(event, user_id):

    state = {
        "mode": "新增演出",
        "step": "artist",
        "data": {},
    }

    set_state(
        user_id,
        state
    )

    reply_message(
        event,
        TextSendMessage(
            text=(
                "➕ 新增演出\n\n"
                "請輸入藝人\n\n"
                "例如：SEVENTEEN"
            ),
            quick_reply=simple_quick_reply([
                ("❌ 取消", "取消")
            ])
        )
    )

    return True


# =========================================================
# 新增演出主流程
# =========================================================

def handle_add_show_flow(event, text, user_id):

    state = get_state(user_id)

    # -----------------------------------------------------
    # 沒有狀態
    # -----------------------------------------------------

    if not isinstance(state, dict):

        print(
            "⚠️ 新增流程找不到 state：",
            repr(state),
            flush=True
        )

        return False

    # -----------------------------------------------------
    # 不是新增演出
    # -----------------------------------------------------

    if state.get("mode") != "新增演出":
        return False

    # -----------------------------------------------------
    # 取得目前資料
    # -----------------------------------------------------

    data = state.setdefault(
        "data",
        {}
    )

    step = state.get("step")

    print(
        "DEBUG 新增流程：",
        "step =", repr(step),
        "text =", repr(text),
        flush=True
    )

    # =====================================================
    # 取消
    #
    # 自訂注意事項中的取消：
    # 只取消「自訂輸入」，回到注意事項選單
    # =====================================================

    if text == "取消" and step == "custom_reminder":

        state["step"] = "reminder"

        set_state(
            user_id,
            state
        )

        reply_message(
            event,
            TextSendMessage(
                text=reminder_message(
                    state.setdefault(
                        "selected_reminders",
                        []
                    )
                ),
                quick_reply=reminder_quick_reply()
            )
        )

        return True

    # =====================================================
    # 一般取消
    # =====================================================

    if text == "取消":

        clear_state(user_id)

        reply_message(
            event,
            TextSendMessage(
                text="已取消新增演出"
            )
        )

        return True

    # =====================================================
    # 藝人
    # =====================================================

    if step == "artist":

        text = text.strip()

        if not text:

            reply_message(
                event,
                TextSendMessage(
                    text="❌ 藝人名稱不可空白\n\n請重新輸入藝人"
                )
            )

            return True

        data["藝人"] = text

        state["step"] = "activity"

        set_state(
            user_id,
            state
        )

        reply_message(
            event,
            TextSendMessage(
                text="🎤 請選擇活動類型",
                quick_reply=activity_quick_reply()
            )
        )

        return True

    # =====================================================
    # 活動
    # =====================================================

    if step == "activity":

        if text not in ACTIVITY_VALUES:

            reply_message(
                event,
                TextSendMessage(
                    text="請使用下方按鈕選擇活動類型",
                    quick_reply=activity_quick_reply()
                )
            )

            return True

        data["活動"] = text

        state["step"] = "activity_name"

        set_state(
            user_id,
            state
        )

        reply_message(
            event,
            TextSendMessage(
                text=(
                    "✨ 請輸入活動名稱\n\n"
                    "例如：BE THE SUN\n\n"
                    "沒有可按略過"
                ),
                quick_reply=simple_quick_reply([
                    ("➖ 略過", "略過"),
                    ("❌ 取消", "取消")
                ])
            )
        )

        return True

    # =====================================================
    # 活動名稱
    # =====================================================

    if step == "activity_name":

        data["活動名稱"] = (
            ""
            if text == "略過"
            else text.strip()
        )

        state["step"] = "show_date"

        set_state(
            user_id,
            state
        )

        reply_message(
            event,
            TextSendMessage(
                text=(
                    "📅 請輸入演出日期\n\n"
                    "例如：10/1\n"
                    "或：2026/10/1"
                ),
                quick_reply=simple_quick_reply([
                    ("❌ 取消", "取消")
                ])
            )
        )

        return True

    # =====================================================
    # 演出日期
    # =====================================================

    if step == "show_date":

        try:

            data["演出日期"] = normalize_show_date(
                text
            )

        except ValueError:

            reply_message(
                event,
                TextSendMessage(
                    text=(
                        "❌ 日期格式不正確\n\n"
                        "請輸入：10/1\n"
                        "或：2026/10/1"
                    ),
                    quick_reply=simple_quick_reply([
                        ("❌ 取消", "取消")
                    ])
                )
            )

            return True

        state["step"] = "ticket_time"

        set_state(
            user_id,
            state
        )

        reply_message(
            event,
            TextSendMessage(
                text=(
                    "🕒 請輸入搶票時間\n\n"
                    "例如：9/1 12:00\n"
                    "或：2026/9/1 12:00"
                ),
                quick_reply=simple_quick_reply([
                    ("❌ 取消", "取消")
                ])
            )
        )

        return True

    # =====================================================
    # 搶票時間
    # =====================================================

    if step == "ticket_time":

        try:

            data["搶票時間"] = normalize_ticket_time(
                text
            )

        except ValueError:

            reply_message(
                event,
                TextSendMessage(
                    text=(
                        "❌ 搶票時間格式不正確\n\n"
                        "請輸入：9/1 12:00"
                    ),
                    quick_reply=simple_quick_reply([
                        ("❌ 取消", "取消")
                    ])
                )
            )

            return True

        state["step"] = "platform"

        set_state(
            user_id,
            state
        )

        reply_message(
            event,
            TextSendMessage(
                text="🌐 請選擇或直接輸入售票平台",
                quick_reply=simple_quick_reply([
                    ("拓元", "拓元"),
                    ("KKTIX", "KKTIX"),
                    ("ibon", "ibon"),
                    ("寬宏", "寬宏"),
                    ("年代", "年代"),
                    ("❌ 取消", "取消")
                ])
            )
        )

        return True

    # =====================================================
    # 售票平台
    # =====================================================

    if step == "platform":

        text = text.strip()

        if not text:

            reply_message(
                event,
                TextSendMessage(
                    text="❌ 售票平台不可空白\n\n請重新輸入"
                )
            )

            return True

        data["售票平台"] = text

        state["step"] = "ticket_url"

        set_state(
            user_id,
            state
        )

        reply_message(
            event,
            TextSendMessage(
                text=(
                    "🔗 請輸入售票網址\n\n"
                    "例如：\n"
                    "https://kktix.com/events/xxxxx\n\n"
                    "沒有網址可按略過"
                ),
                quick_reply=simple_quick_reply([
                    ("➖ 略過", "略過"),
                    ("❌ 取消", "取消")
                ])
            )
        )

        return True

    # =====================================================
    # 售票網址
    # =====================================================

    if step == "ticket_url":

        data["售票網址"] = (
            ""
            if text == "略過"
            else text.strip()
        )

        state["step"] = "price"

        set_state(
            user_id,
            state
        )

        reply_message(
            event,
            TextSendMessage(
                text=(
                    "💰 請輸入價格與張數\n\n"
                    "例如：3800*2"
                ),
                quick_reply=simple_quick_reply([
                    ("❌ 取消", "取消")
                ])
            )
        )

        return True

    # =====================================================
    # 價格張數
    # =====================================================

    if step == "price":

        text = text.strip()

        if not text:

            reply_message(
                event,
                TextSendMessage(
                    text="❌ 價格與張數不可空白\n\n請重新輸入\n例如：3800*2"
                )
            )

            return True

        data["價格張數"] = text

        state["step"] = "sale_stage"

        set_state(
            user_id,
            state
        )

        reply_message(
            event,
            TextSendMessage(
                text="🚩 請選擇售票階段",
                quick_reply=simple_quick_reply([
                    ("會員預售", "會員預售"),
                    ("卡友優先", "卡友優先"),
                    ("公售", "公售"),
                    ("❌ 取消", "取消")
                ])
            )
        )

        return True

    # =====================================================
    # 售票階段
    # =====================================================

    if step == "sale_stage":

        if text not in [
            "會員預售",
            "卡友優先",
            "公售",
        ]:

            reply_message(
                event,
                TextSendMessage(
                    text="請使用下方按鈕選擇售票階段",
                    quick_reply=simple_quick_reply([
                        ("會員預售", "會員預售"),
                        ("卡友優先", "卡友優先"),
                        ("公售", "公售"),
                        ("❌ 取消", "取消")
                    ])
                )
            )

            return True

        data["售票階段"] = text

        state["step"] = "member"

        set_state(
            user_id,
            state
        )

        reply_message(
            event,
            TextSendMessage(
                text=(
                    "🔑 請輸入會員資訊\n\n"
                    "例如：\n"
                    "BRxxxxxxxxx\n"
                    "ACE會員\n"
                    "沒有可按略過"
                ),
                quick_reply=simple_quick_reply([
                    ("➖ 略過", "略過"),
                    ("❌ 取消", "取消")
                ])
            )
        )

        return True

    # =====================================================
    # 會員資訊
    # =====================================================

    if step == "member":

        data["會員資訊"] = (
            ""
            if text == "略過"
            else text.strip()
        )

        state["step"] = "reminder"

        state["selected_reminders"] = []

        set_state(
            user_id,
            state
        )

        reply_message(
            event,
            TextSendMessage(
                text=reminder_message([]),
                quick_reply=reminder_quick_reply()
            )
        )

        return True

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

            data["注意事項"] = ""

            state.pop(
                "selected_reminders",
                None
            )

            state["step"] = "pickup_date"

            set_state(
                user_id,
                state
            )

            reply_message(
                event,
                TextSendMessage(
                    text=(
                        "📦 請輸入取票日期\n\n"
                        "例如：5天前\n"
                        "或：9/25\n\n"
                        "沒有取票提醒可按略過"
                    ),
                    quick_reply=simple_quick_reply([
                        ("3天前", "3天前"),
                        ("5天前", "5天前"),
                        ("7天前", "7天前"),
                        ("➖ 略過", "略過"),
                        ("❌ 取消", "取消")
                    ])
                )
            )

            return True

        # -------------------------------------------------
        # 完成
        # -------------------------------------------------

        if text == "完成":

            if not selected:

                reply_message(
                    event,
                    TextSendMessage(
                        text="請至少選擇一項，或按「略過」",
                        quick_reply=reminder_quick_reply()
                    )
                )

                return True

            data["注意事項"] = "\n".join(
                selected
            )

            state.pop(
                "selected_reminders",
                None
            )

            state["step"] = "pickup_date"

            set_state(
                user_id,
                state
            )

            reply_message(
                event,
                TextSendMessage(
                    text=(
                        "📦 請輸入取票日期\n\n"
                        "例如：5天前\n"
                        "或：9/25\n\n"
                        "沒有取票提醒可按略過"
                    ),
                    quick_reply=simple_quick_reply([
                        ("3天前", "3天前"),
                        ("5天前", "5天前"),
                        ("7天前", "7天前"),
                        ("➖ 略過", "略過"),
                        ("❌ 取消", "取消")
                    ])
                )
            )

            return True

        # -------------------------------------------------
        # 自訂
        #
        # theme.py 傳進來的是「自訂」
        # -------------------------------------------------

        if text == "自訂":

            state["step"] = "custom_reminder"

            set_state(
                user_id,
                state
            )

            reply_message(
                event,
                TextSendMessage(
                    text=(
                        "✏️ 請輸入注意事項\n\n"
                        "例如：記得帶身分證\n"
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

                selected.append(text)

            set_state(
                user_id,
                state
            )

            reply_message(
                event,
                TextSendMessage(
                    text=reminder_message(
                        selected
                    ),
                    quick_reply=reminder_quick_reply()
                )
            )

            return True

        # -------------------------------------------------
        # 不認識的輸入
        # 不清除 state
        # -------------------------------------------------

        reply_message(
            event,
            TextSendMessage(
                text=(
                    "⚠️ 請使用下方按鈕選擇注意事項，"
                    "或按「✏️ 自訂」自行輸入。"
                ),
                quick_reply=reminder_quick_reply()
            )
        )

        return True

    # =====================================================
    # 自訂注意事項
    # =====================================================

    if step == "custom_reminder":

        selected = state.setdefault(
            "selected_reminders",
            []
        )

        text = text.strip()

        # -------------------------------------------------
        # 空白
        # -------------------------------------------------

        if not text:

            reply_message(
                event,
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

        # -------------------------------------------------
        # 加入自訂注意事項
        # -------------------------------------------------

        if text not in selected:

            selected.append(text)

        state["step"] = "reminder"

        set_state(
            user_id,
            state
        )

        reply_message(
            event,
            TextSendMessage(
                text=reminder_message(
                    selected
                ),
                quick_reply=reminder_quick_reply()
            )
        )

        return True

    # =====================================================
    # 取票日期
    # =====================================================

    if step == "pickup_date":

        # -------------------------------------------------
        # 略過
        # -------------------------------------------------

        if text == "略過":

            data["取票日期"] = ""

            state["step"] = "note"

            set_state(
                user_id,
                state
            )

            reply_message(
                event,
                TextSendMessage(
                    text=(
                        "📝 請輸入備註\n\n"
                        "例如：\n"
                        "帳號xxxxxxx\n"
                        "密碼xxxxxxx\n"
                        "實名制資料\n\n"
                        "沒有備註可按略過"
                    ),
                    quick_reply=simple_quick_reply([
                        ("➖ 略過", "略過"),
                        ("❌ 取消", "取消")
                    ])
                )
            )

            return True

        # -------------------------------------------------
        # 正常日期
        # -------------------------------------------------

        try:

            data["取票日期"] = normalize_pickup_date(
                text,
                data["演出日期"]
            )

        except ValueError:

            reply_message(
                event,
                TextSendMessage(
                    text=(
                        "❌ 取票日期格式不正確\n\n"
                        "請輸入：5天前\n"
                        "或：2026/9/25"
                    ),
                    quick_reply=simple_quick_reply([
                        ("3天前", "3天前"),
                        ("5天前", "5天前"),
                        ("7天前", "7天前"),
                        ("➖ 略過", "略過"),
                        ("❌ 取消", "取消")
                    ])
                )
            )

            return True

        state["step"] = "note"

        set_state(
            user_id,
            state
        )

        reply_message(
            event,
            TextSendMessage(
                text=(
                    "📝 請輸入備註\n\n"
                    "例如：\n"
                    "帳號xxxxxxx\n"
                    "密碼xxxxxxx\n"
                    "實名制資料\n\n"
                    "沒有備註可按略過"
                ),
                quick_reply=simple_quick_reply([
                    ("➖ 略過", "略過"),
                    ("❌ 取消", "取消")
                ])
            )
        )

        return True

    # =====================================================
    # 備註
    # =====================================================

    if step == "note":

        data["備註"] = (
            ""
            if text == "略過"
            else text.strip()
        )

        state["step"] = "confirm"

        set_state(
            user_id,
            state
        )

        reply = (
            "📋 請確認新增資料\n"
            "──────────\n"
            f"🎤 {data.get('藝人', '')}\n"
            f"🏷️ {data.get('活動', '')}\n"
        )

        if data.get("活動名稱"):

            reply += (
                f"✨ {data['活動名稱']}\n"
            )

        reply += (
            f"📅 {format_show_dates(data['演出日期'])}\n"
            f"🕒 {format_datetime(data['搶票時間'])}\n"
            f"🌐 {data['售票平台']}\n"
        )

        if data.get("售票網址"):

            reply += (
                f"🔗 {data['售票網址']}\n"
            )

        reply += (
            f"💰 {data['價格張數']}\n"
        )

        if data.get("售票階段"):

            reply += (
                f"🚩 {data['售票階段']}\n"
            )

        if data.get("會員資訊"):

            reply += (
                f"🔑 {data['會員資訊']}\n"
            )

        if data.get("注意事項"):

            reply += (
                "🔔 注意事項\n"
                + "\n".join(
                    f"• {item}"
                    for item in data["注意事項"].splitlines()
                )
                + "\n"
            )

        reply += (
            f"📦 {data.get('取票日期') or '未設定'}\n"
            f"📝 {data.get('備註') or '無'}"
        )

        reply_message(
            event,
            TextSendMessage(
                text=reply,
                quick_reply=simple_quick_reply([
                    ("✅ 確認新增", "確認新增"),
                    ("🔄 重新填寫", "重新填寫"),
                    ("❌ 取消", "取消")
                ])
            )
        )

        return True

    # =====================================================
    # 確認新增
    # =====================================================

    if step == "confirm":

        # -------------------------------------------------
        # 如果之前 DB 已成功，但 LINE 成功訊息沒送出去
        # 不再次 insert_show
        # -------------------------------------------------

        inserted_show = state.get(
            "inserted_show"
        )

        if inserted_show:

            if text == "確認新增":

                success = (
                    "✅ 已新增演出\n"
                    "──────────\n"
                    f"🎤 {inserted_show['藝人']}\n"
                    f"🏷️ {inserted_show['活動']}\n"
                )

                if inserted_show.get("活動名稱"):

                    success += (
                        f"✨ {inserted_show['活動名稱']}\n"
                    )

                success += (
                    f"📅 {format_show_dates(inserted_show['演出日期'])}\n"
                    f"🕒 {format_datetime(inserted_show['搶票時間'])}"
                )

                if reply_message(
                    event,
                    TextSendMessage(
                        text=success
                    )
                ):

                    clear_state(
                        user_id
                    )

                return True

            if text == "取消":

                clear_state(
                    user_id
                )

                reply_message(
                    event,
                    TextSendMessage(
                        text="已新增成功，不需要再次新增。"
                    )
                )

                return True

        # -------------------------------------------------
        # 重新填寫
        # -------------------------------------------------

        if text == "重新填寫":

            state["step"] = "artist"

            state["data"] = {}

            state.pop(
                "selected_reminders",
                None
            )

            state.pop(
                "inserted_show",
                None
            )

            state.pop(
                "pending_show",
                None
            )

            set_state(
                user_id,
                state
            )

            reply_message(
                event,
                TextSendMessage(
                    text="請重新輸入藝人",
                    quick_reply=simple_quick_reply([
                        ("❌ 取消", "取消")
                    ])
                )
            )

            return True

        # -------------------------------------------------
        # 不是確認新增
        # -------------------------------------------------

        if text != "確認新增":

            reply_message(
                event,
                TextSendMessage(
                    text="請使用下方按鈕確認",
                    quick_reply=simple_quick_reply([
                        ("✅ 確認新增", "確認新增"),
                        ("🔄 重新填寫", "重新填寫"),
                        ("❌ 取消", "取消")
                    ])
                )
            )

            return True

        # -------------------------------------------------
        # 建立演出資料
        # -------------------------------------------------

        show = {
            "藝人": data.get("藝人", ""),
            "活動": data.get("活動", ""),
            "活動名稱": data.get("活動名稱", ""),

            "演出日期": data.get("演出日期", ""),
            "搶票時間": data.get("搶票時間", ""),
            "售票平台": data.get("售票平台", ""),
            "售票網址": data.get("售票網址", ""),
            "價格張數": data.get("價格張數", ""),
            "會員資訊": data.get("會員資訊", ""),
            "注意事項": data.get("注意事項", ""),
            "售票階段": data.get("售票階段", ""),
            "取票日期": data.get("取票日期", ""),
            "備註": data.get("備註", ""),

            "搶票狀態": "待搶票",
            "取票狀態": "未取票",
            "搶票大師": "",
            "取票人": "",

            "提醒": {
                "前一天": False,
                "30分鐘": False,
                "10分鐘": False,
                "取票": False,
                "演出日": False,
            },
        }

        # -------------------------------------------------
        # 先保存待新增資料
        # -------------------------------------------------

        state["pending_show"] = show

        set_state(
            user_id,
            state
        )

        # -------------------------------------------------
        # 寫入資料庫
        # -------------------------------------------------

        try:

            result = insert_show(
                show
            )

            # 有些 insert_show 可能回傳 None
            # 如果沒有回傳資料，就繼續使用原 show
            if result is not None:

                show = result

        except Exception as e:

            print(
                "新增演出失敗：",
                repr(e),
                flush=True
            )

            # state 不清除
            # pending_show 保留
            set_state(
                user_id,
                state
            )

            reply_message(
                event,
                TextSendMessage(
                    text=(
                        "❌ 新增演出失敗\n\n"
                        "資料沒有被刪除。\n"
                        "請按「再試一次」重新寫入。"
                    ),
                    quick_reply=simple_quick_reply([
                        ("✅ 再試一次", "確認新增"),
                        ("🔄 重新填寫", "重新填寫"),
                        ("❌ 取消", "取消")
                    ])
                )
            )

            return True

        # -------------------------------------------------
        # DB 成功
        #
        # 先保存 inserted_show
        # 避免 LINE 回覆失敗時重複 insert
        # -------------------------------------------------

        state["inserted_show"] = show

        state.pop(
            "pending_show",
            None
        )

        set_state(
            user_id,
            state
        )

        # -------------------------------------------------
        # 成功訊息
        # -------------------------------------------------

        success = (
            "✅ 已新增演出\n"
            "──────────\n"
            f"🎤 {show['藝人']}\n"
            f"🏷️ {show['活動']}\n"
        )

        if show.get("活動名稱"):

            success += (
                f"✨ {show['活動名稱']}\n"
            )

        success += (
            f"📅 {format_show_dates(show['演出日期'])}\n"
            f"🕒 {format_datetime(show['搶票時間'])}"
        )

        # -------------------------------------------------
        # 發送成功訊息
        # -------------------------------------------------

        if not reply_message(
            event,
            TextSendMessage(
                text=success
            )
        ):

            print(
                "⚠️ 新增成功，但成功訊息沒有送出。",
                flush=True
            )

            # 不 clear_state
            # inserted_show 還在
            return True

        # -------------------------------------------------
        # 成功送出後才清除
        # -------------------------------------------------

        clear_state(
            user_id
        )

        return True

    # =====================================================
    # 狀態異常
    #
    # ★ 絕對不要 clear_state
    # =====================================================

    print(
        "⚠️ 新增流程未處理：",
        "step =", repr(step),
        "text =", repr(text),
        "state =", repr(state),
        flush=True
    )

    # 保留目前狀態
    set_state(
        user_id,
        state
    )

    reply_message(
        event,
        TextSendMessage(
            text=(
                "⚠️ 這個輸入目前無法處理。\n\n"
                "目前新增資料仍然保留，"
                "請繼續操作或按「取消」結束新增。"
            ),
            quick_reply=simple_quick_reply([
                ("❌ 取消", "取消")
            ])
        )
    )

    return True
    set_state(
        user_id,
        {
            "mode": "新增演出",
            "step": "artist",
            "data": {}
        }
    )

    config.line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=(
                "➕ 新增演出\n\n"
                "請輸入藝人\n\n"
                "例如：SEVENTEEN"
            ),
            quick_reply=simple_quick_reply([
                ("❌ 取消", "取消")
            ])
        )
    )

    return True


def handle_add_show_flow(event, text, user_id):

    state = get_state(user_id)

    if not isinstance(state, dict):
        return False

    if state.get("mode") != "新增演出":
        return False

    if text == "取消":

        clear_state(user_id)

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="已取消新增演出"
            )
        )

        return True

    data = state.setdefault("data", {})
    step = state.get("step")

    # =====================
    # 藝人
    # =====================

    if step == "artist":

        data["藝人"] = text
        state["step"] = "activity"

        # 立即保存目前進度
        set_state(user_id, state)

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=(
                    "🎤 請選擇活動類型"
                ),
                quick_reply=activity_quick_reply()
            )
        )

        return True

    # =====================
    # 活動
    # =====================

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

        data["活動"] = text
        state["step"] = "activity_name"

        # 立即保存目前進度
        set_state(user_id, state)

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=(
                    "✨ 請輸入活動名稱\n\n"
                    "例如：BE THE SUN\n\n"
                    "沒有可按略過"
                ),
                quick_reply=simple_quick_reply([
                    ("➖ 略過", "略過"),
                    ("❌ 取消", "取消"),
                ])
            )
        )

        return True

    # =====================
    # 活動名稱
    # =====================

    if step == "activity_name":

        data["活動名稱"] = "" if text == "略過" else text
        state["step"] = "show_date"

        # 立即保存目前進度
        set_state(user_id, state)

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=(
                    "📅 請輸入演出日期\n\n"
                    "例如：10/1\n"
                    "或：2026/10/1"
                ),
                quick_reply=simple_quick_reply([
                    ("❌ 取消", "取消")
                ])
            )
        )

        return True

    # =====================
    # 演出日期
    # =====================

    if step == "show_date":

        try:

            data["演出日期"] = normalize_show_date(text)

        except ValueError:

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=(
                        "❌ 日期格式不正確\n\n"
                        "請輸入：10/1\n"
                        "或：2026/10/1"
                    ),
                    quick_reply=simple_quick_reply([
                        ("❌ 取消", "取消")
                    ])
                )
            )

            return True

        state["step"] = "ticket_time"

        # 立即保存目前進度
        set_state(user_id, state)

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=(
                    "🕒 請輸入搶票時間\n\n"
                    "例如：9/1 12:00\n"
                    "或：2026/9/1 12:00"
                ),
                quick_reply=simple_quick_reply([
                    ("❌ 取消", "取消")
                ])
            )
        )

        return True

    # =====================
    # 搶票時間
    # =====================

    if step == "ticket_time":

        try:

            data["搶票時間"] = normalize_ticket_time(text)

        except ValueError:

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=(
                        "❌ 搶票時間格式不正確\n\n"
                        "請輸入：9/1 12:00"
                    ),
                    quick_reply=simple_quick_reply([
                        ("❌ 取消", "取消")
                    ])
                )
            )

            return True

        state["step"] = "platform"

        # 立即保存目前進度
        set_state(user_id, state)

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="🌐 請選擇或直接輸入售票平台",
                quick_reply=simple_quick_reply([
                    ("拓元", "拓元"),
                    ("KKTIX", "KKTIX"),
                    ("ibon", "ibon"),
                    ("寬宏", "寬宏"),
                    ("年代", "年代"),
                    ("❌ 取消", "取消")
                ])
            )
        )

        return True

    # =====================
    # 售票平台
    # =====================

    if step == "platform":

        data["售票平台"] = text
        state["step"] = "ticket_url"

        # 立即保存目前進度
        set_state(user_id, state)

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=(
                    "🔗 請輸入售票網址\n\n"
                    "例如：\n"
                    "https://kktix.com/events/xxxxx\n\n"
                    "沒有網址可按略過"
                ),
                quick_reply=simple_quick_reply([
                    ("➖ 略過", "略過"),
                    ("❌ 取消", "取消")
                ])
            )
        )

        return True

    # =====================
    # 售票網址
    # =====================

    if step == "ticket_url":

        data["售票網址"] = (
            ""
            if text == "略過"
            else text.strip()
        )

        state["step"] = "price"

        # 立即保存目前進度
        set_state(user_id, state)

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=(
                    "💰 請輸入價格與張數\n\n"
                    "例如：3800*2"
                ),
                quick_reply=simple_quick_reply([
                    ("❌ 取消", "取消")
                ])
            )
        )

        return True

    # =====================
    # 價格張數
    # =====================

    if step == "price":

        data["價格張數"] = text
        state["step"] = "sale_stage"

        # 立即保存目前進度
        set_state(user_id, state)

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="🚩 請選擇售票階段",
                quick_reply=simple_quick_reply([
                    ("會員預售", "會員預售"),
                    ("卡友優先", "卡友優先"),
                    ("公售", "公售"),
                    ("❌ 取消", "取消"),
                ])
            )
        )

        return True

    # =====================
    # 售票階段
    # =====================

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

        data["售票階段"] = text

        state["step"] = "member"

        # 立即保存目前進度
        set_state(user_id, state)

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=(
                    "🔑 請輸入會員資訊\n\n"
                    "例如：\n"
                    "BRxxxxxxxxx\n"
                    "ACE會員\n"
                    "沒有可按略過"
                ),
                quick_reply=simple_quick_reply([
                    ("➖ 略過", "略過"),
                    ("❌ 取消", "取消"),
                ])
            )
        )

        return True

    # =====================
    # 會員資訊
    # =====================

    if step == "member":

        data["會員資訊"] = "" if text == "略過" else text

        state["step"] = "reminder"
        state["selected_reminders"] = []

        # 立即保存目前進度
        set_state(user_id, state)

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=reminder_message([]),
                quick_reply=reminder_quick_reply(),
            )
        )

        return True

    # =====================
    # 注意事項
    # =====================

    if step == "reminder":

        selected = state.setdefault(
            "selected_reminders",
            []
        )

        if text == "略過":

            data["注意事項"] = ""

            state.pop(
                "selected_reminders",
                None,
            )

            state["step"] = "pickup_date"

            # 立即保存目前進度
            set_state(user_id, state)

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=(
                        "📦 請輸入取票日期\n\n"
                        "例如：5天前\n"
                        "或：9/25\n\n"
                        "沒有取票提醒可按略過"
                    ),
                    quick_reply=simple_quick_reply([
                        ("3天前", "3天前"),
                        ("5天前", "5天前"),
                        ("7天前", "7天前"),
                        ("➖ 略過", "略過"),
                        ("❌ 取消", "取消"),
                    ])
                )
            )

            return True

        if text == "完成":

            if not selected:

                config.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="請至少選擇一項，或按「略過」",
                        quick_reply=reminder_quick_reply(),
                    )
                )

                return True

            data["注意事項"] = "\n".join(
                selected
            )

            state.pop(
                "selected_reminders",
                None,
            )

            state["step"] = "pickup_date"

            # 立即保存目前進度
            set_state(user_id, state)

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=(
                        "📦 請輸入取票日期\n\n"
                        "例如：5天前\n"
                        "或：9/25\n\n"
                        "沒有取票提醒可按略過"
                    ),
                    quick_reply=simple_quick_reply([
                        ("3天前", "3天前"),
                        ("5天前", "5天前"),
                        ("7天前", "7天前"),
                        ("➖ 略過", "略過"),
                        ("❌ 取消", "取消"),
                    ])
                )
            )

            return True

        if text == "自訂":

            state["step"] = "custom_reminder"

            # 立即保存目前進度
            set_state(user_id, state)

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="請輸入注意事項",
                    quick_reply=simple_quick_reply([
                        ("❌ 取消", "取消"),
                    ])
                )
            )

            return True

        if text in REMINDER_OPTIONS:

            if text not in selected:

                selected.append(text)

            # 保存已選擇的提醒
            set_state(user_id, state)

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=reminder_message(
                        selected
                    ),
                    quick_reply=reminder_quick_reply(),
                )
            )

            return True

    # =====================
    # 自訂注意事項
    # =====================

    if step == "custom_reminder":

        selected = state.setdefault(
            "selected_reminders",
            []
        )

        text = text.strip()

        if not text:

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="注意事項不可空白"
                )
            )

            return True

        if text not in selected:

            selected.append(text)

        state["step"] = "reminder"

        # 立即保存目前進度
        set_state(user_id, state)

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=reminder_message(
                    selected
                ),
                quick_reply=reminder_quick_reply(),
            )
        )

        return True

    # =====================
    # 取票日期
    # =====================

    if step == "pickup_date":

        # 原本這裡有「略過」按鈕，
        # 但程式沒有處理，會直接進 normalize_pickup_date。
        if text == "略過":

            data["取票日期"] = ""

            state["step"] = "note"

            # 立即保存目前進度
            set_state(user_id, state)

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=(
                        "📝 請輸入備註\n\n"
                        "例如：\n"
                        "帳號xxxxxxx\n"
                        "密碼xxxxxxx\n"
                        "實名制資料\n\n"
                        "沒有備註可按略過"
                    ),
                    quick_reply=simple_quick_reply([
                        ("➖ 略過", "略過"),
                        ("❌ 取消", "取消")
                    ])
                )
            )

            return True

        try:

            data["取票日期"] = normalize_pickup_date(
                text,
                data["演出日期"]
            )

        except ValueError:

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=(
                        "❌ 取票日期格式不正確\n\n"
                        "請輸入：5天前\n"
                        "或：2026/9/25"
                    ),
                    quick_reply=simple_quick_reply([
                        ("3天前", "3天前"),
                        ("5天前", "5天前"),
                        ("7天前", "7天前"),
                        ("➖ 略過", "略過"),
                        ("❌ 取消", "取消")
                    ])
                )
            )

            return True

        state["step"] = "note"

        # 立即保存目前進度
        set_state(user_id, state)

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=(
                    "📝 請輸入備註\n\n"
                    "例如：\n"
                    "帳號xxxxxxx\n"
                    "密碼xxxxxxx\n"
                    "實名制資料\n\n"
                    "沒有備註可按略過"
                ),
                quick_reply=simple_quick_reply([
                    ("➖ 略過", "略過"),
                    ("❌ 取消", "取消")
                ])
            )
        )

        return True

    # =====================
    # 備註
    # =====================

    if step == "note":

        data["備註"] = "" if text == "略過" else text
        state["step"] = "confirm"

        # 立即保存目前進度
        set_state(user_id, state)

        reply = (
            "📋 請確認新增資料\n"
            "──────────\n"
            f"🎤 {data['藝人']}\n"
            f"🏷️ {data['活動']}\n"
        )

        if data.get("活動名稱"):
            reply += f"✨ {data['活動名稱']}\n"

        reply += (
            f"📅 {format_show_dates(data['演出日期'])}\n"
            f"🕒 {format_datetime(data['搶票時間'])}\n"
            f"🌐 {data['售票平台']}\n"
        )

        if data.get("售票網址"):
            reply += f"🔗 {data['售票網址']}\n"

        reply += (
            f"💰 {data['價格張數']}\n"
        )

        if data.get("售票階段"):
            reply += f"🚩 {data['售票階段']}\n"

        if data.get("會員資訊"):
            reply += f"🔑 {data['會員資訊']}\n"

        if data.get("注意事項"):
            reply += (
                "🔔 注意事項\n"
                + "\n".join(
                    f"• {item}"
                    for item in data["注意事項"].splitlines()
                )
                + "\n"
            )

        reply += (
            f"📦 {data.get('取票日期') or '未設定'}\n"
            f"📝 {data.get('備註') or '無'}"
        )

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=reply,
                quick_reply=simple_quick_reply([
                    ("✅ 確認新增", "確認新增"),
                    ("🔄 重新填寫", "重新填寫"),
                    ("❌ 取消", "取消")
                ])
            )
        )

        return True

    # =====================
    # 確認新增
    # =====================

    if step == "confirm":

        # ---------------------------------
        # 已經成功新增，只是成功訊息沒送出去
        # 避免再次 insert_show 造成重複資料
        # ---------------------------------

        inserted_show = state.get("inserted_show")

        if inserted_show:

            if text == "確認新增":

                success = (
                    "✅ 已新增演出\n"
                    "──────────\n"
                    f"🎤 {inserted_show['藝人']}\n"
                    f"🏷️ {inserted_show['活動']}\n"
                )

                if inserted_show.get("活動名稱"):
                    success += (
                        f"✨ {inserted_show['活動名稱']}\n"
                    )

                success += (
                    f"📅 {format_show_dates(inserted_show['演出日期'])}\n"
                    f"🕒 {format_datetime(inserted_show['搶票時間'])}"
                )

                try:

                    config.line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text=success
                        )
                    )

                except Exception as e:

                    print(
                        "新增成功訊息再次推播失敗：",
                        repr(e),
                        flush=True
                    )

                    return True

                clear_state(user_id)

                return True

            if text == "取消":

                clear_state(user_id)

                config.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="已新增成功，不需要再次新增。"
                    )
                )

                return True

        # ---------------------------------
        # 重新填寫
        # ---------------------------------

        if text == "重新填寫":

            state["step"] = "artist"
            state["data"] = {}

            state.pop(
                "selected_reminders",
                None,
            )

            state.pop(
                "inserted_show",
                None,
            )

            # 保存重新填寫狀態
            set_state(user_id, state)

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="請重新輸入藝人",
                    quick_reply=simple_quick_reply([
                        ("❌ 取消", "取消")
                    ])
                )
            )

            return True

        # ---------------------------------
        # 不是確認新增
        # ---------------------------------

        if text != "確認新增":

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="請使用下方按鈕確認",
                    quick_reply=simple_quick_reply([
                        ("✅ 確認新增", "確認新增"),
                        ("🔄 重新填寫", "重新填寫"),
                        ("❌ 取消", "取消")
                    ])
                )
            )

            return True

        # ---------------------------------
        # 建立演出資料
        # ---------------------------------

        show = {
            "藝人": data.get("藝人", ""),
            "活動": data.get("活動", ""),
            "活動名稱": data.get("活動名稱", ""),

            "演出日期": data.get("演出日期", ""),
            "搶票時間": data.get("搶票時間", ""),
            "售票平台": data.get("售票平台", ""),
            "售票網址": data.get("售票網址", ""),
            "價格張數": data.get("價格張數", ""),
            "會員資訊": data.get("會員資訊", ""),
            "注意事項": data.get("注意事項", ""),
            "售票階段": data.get("售票階段", ""),
            "取票日期": data.get("取票日期", ""),
            "備註": data.get("備註", ""),

            "搶票狀態": "待搶票",
            "取票狀態": "未取票",
            "搶票大師": "",
            "取票人": "",

            "提醒": {
                "前一天": False,
                "30分鐘": False,
                "10分鐘": False,
                "取票": False,
                "演出日": False,
            },
        }

        # ---------------------------------
        # 先保存待新增資料
        # 如果 insert_show 中途出錯，
        # state 裡還有完整資料可以重試
        # ---------------------------------

        state["pending_show"] = show
        set_state(user_id, state)

        # ---------------------------------
        # 寫入資料庫
        # ---------------------------------

        try:

            show = insert_show(show)

        except Exception as e:

            print(
                "新增演出失敗：",
                repr(e),
                flush=True
            )

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=(
                        "❌ 新增演出失敗\n\n"
                        f"{e}\n\n"
                        "資料還在，請再按一次「確認新增」重試。"
                    ),
                    quick_reply=simple_quick_reply([
                        ("✅ 再試一次", "確認新增"),
                        ("🔄 重新填寫", "重新填寫"),
                        ("❌ 取消", "取消"),
                    ])
                )
            )

            return True

        # ---------------------------------
        # insert_show 成功
        #
        # 先把已新增資料保存起來。
        # 這樣即使下面 LINE 回覆失敗，
        # 下次也不會再次 insert_show。
        # ---------------------------------

        state["inserted_show"] = show
        state.pop("pending_show", None)

        # 注意：這裡先保存「已新增」狀態
        set_state(user_id, state)

        success = (
            "✅ 已新增演出\n"
            "──────────\n"
            f"🎤 {show['藝人']}\n"
            f"🏷️ {show['活動']}\n"
        )

        if show.get("活動名稱"):
            success += f"✨ {show['活動名稱']}\n"

        success += (
            f"📅 {format_show_dates(show['演出日期'])}\n"
            f"🕒 {format_datetime(show['搶票時間'])}"
        )

        # ---------------------------------
        # 發送成功訊息
        # ---------------------------------

        try:

            config.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=success
                )
            )

        except Exception as e:

            print(
                "新增成功訊息推播失敗：",
                repr(e),
                flush=True
            )

            # 不 clear_state
            # 保留 inserted_show，避免重複新增
            return True

        # 成功送出後才清除狀態
        clear_state(user_id)

        return True

    # =====================
    # 狀態異常
    # =====================

    clear_state(user_id)

    config.line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text="❌ 新增狀態異常，請重新操作"
        )
    )

    return True
