line_bot_api = None

GROUP_ID = None

push_mention_message = None


from datetime import datetime, timedelta

from linebot.models import TextSendMessage

from data import (
    supabase,
    load_data,
    save_data,
    update_show,
)

from utils import (
    format_price,
    parse_date,
    parse_datetime,
    format_datetime,
    get_last_show_date,
)

# =====================
# 提醒功能
# =====================

def check_reminders():

    print("提醒檢查執行", datetime.now())

    now = datetime.now() + timedelta(hours=8)

    shows = load_data()

    print("目前演出資料：", shows)

    for show in shows:

        show.setdefault("提醒", {
            "前一天": False,
            "30分鐘": False,
            "10分鐘": False,
            "取票": False,
            "演出日": False
        })

        print(
            "提醒狀態：",
            show["演出名稱"],
            show["提醒"]
        )


        show.setdefault("搶票狀態", "等待搶票")
        show.setdefault("取票狀態", "未取票")


        try:

            ticket_time = parse_datetime(
                show["搶票時間"]
            )


            # 前一天 21:00

            remind_time = (
                ticket_time - timedelta(days=1)
            ).replace(
                hour=21,
                minute=0,
                second=0,
                microsecond=0
            )


            if (
                remind_time <= now <= remind_time + timedelta(minutes=1)
                and not show["提醒"]["前一天"]
            ):

                line_bot_api.push_message(
                    GROUP_ID,
                    TextSendMessage(
                        text=(
                            "⏰ 明日搶票提醒\n\n"
                            f"🎤 {show['演出名稱']}\n"
                            f"🎟 搶票時間：{format_datetime(show['搶票時間'])}\n"
                            f"🌐 售票平台：{show['售票平台']}"
                        )
                    )
                )


                show["提醒"]["前一天"] = True
                update_show(show)


            diff = ticket_time - now

            print("=" * 50)
            print("現在時間：", now)
            print("演出：", show["演出名稱"])
            print("搶票時間：", ticket_time)
            print("剩餘：", diff)
            print("30分鐘：", show["提醒"]["30分鐘"])
            print("10分鐘：", show["提醒"]["10分鐘"])


            # 前30分鐘

            if (
                timedelta(minutes=29)
                <= diff 
                <= timedelta(minutes=30)
                and not show["提醒"]["30分鐘"]
            ):


                print(">>> 發送30分鐘提醒")


                line_bot_api.push_message(
                    GROUP_ID,
                    TextSendMessage(
                        text=(
                            "⏰ 搶票倒數 30 分鐘\n\n"
                            f"🎤 {show['演出名稱']}\n"
                            f"🎟 搶票時間：{format_datetime(show['搶票時間'])}\n"
                            f"🌐 售票平台：{show['售票平台']}\n"
                            f"📝 備註：{show['備註'] if show['備註'] else '無'}"
                        )
                    )
                )


                show["提醒"]["30分鐘"] = True
                update_show(show)


            # 前10分鐘

            if (
                timedelta(minutes=9)
                <= diff 
                <= timedelta(minutes=10)
                and not show["提醒"]["10分鐘"]
            ):

                print(">>> 發送10分鐘提醒")


                line_bot_api.push_message(
                    GROUP_ID,
                    TextSendMessage(
                        text=(
                            "🔐 搶票倒數 10 分鐘\n\n"
                            f"🎤 {show['演出名稱']}\n"
                            f"🎟 搶票時間：{format_datetime(show['搶票時間'])}\n"
                            f"🌐 售票平台：{show['售票平台']}\n"
                            f"💰 價格張數：{format_price(show['價格張數'])}\n"
                            f"📝 備註：{show['備註'] if show['備註'] else '無'}"
                        )
                    )
                )

                show["提醒"]["10分鐘"] = True
                update_show(show)


        except Exception as e:

            print(
                f"提醒錯誤：{e}"
            )


        # 取票提醒
        if show.get("取票日期"):

            pickup_time = parse_datetime(
                show["取票日期"] + " 12:00"
            )

            if (
                pickup_time <= now < pickup_time + timedelta(minutes=1)
                and not show["提醒"]["取票"]
            ):

                participants = [
                    x.strip()
                    for x in show.get("取票人", "").split("、")
                    if x.strip()
                ]

                push_mention_message(
                    GROUP_ID,
                    (
                        "🎫 取票提醒\n\n"
                        f"🎤 {show['演出名稱']}\n"
                        "🎫 可以取票囉～"
                    ),
                    participants
                )

                show["提醒"]["取票"] = True
                save_data(shows)

# =====================
# 今日重點
# =====================

def send_today_summary():

    now = datetime.now() + timedelta(hours=8)
    today = now.date()

    shows = load_data()

    ticket_today = []
    pickup_today = []
    show_today = []
    upcoming = []

    for show in shows:

        # 今天搶票
        try:
            ticket_time = parse_datetime(show["搶票時間"])

            if (
                ticket_time.date() == today
                and show.get("搶票狀態", "等待搶票") == "等待搶票"
            ):
                ticket_today.append(show)

        except:
            pass

        # 今天可取票
        try:
            if (
                show.get("取票日期")
                and parse_date(show["取票日期"]) == today
                and show.get("取票狀態", "未取票") == "未取票"
            ):
                pickup_today.append(show)

        except:
            pass

        # 今天演出
        try:
            if parse_date(show["演出日期"]) == today:
                show_today.append(show)

        except:
            pass

        # 未來7天搶票
        try:

            ticket_time = parse_datetime(show["搶票時間"])

            days = (ticket_time.date() - today).days

            if (
                1 <= days <= 7
                and show.get("搶票狀態", "等待搶票") == "等待搶票"
            ):

                upcoming.append(
                    (
                        ticket_time.date(),
                        f"{ticket_time.strftime('%m/%d')}　🎟 {show['演出名稱']}（{ticket_time.strftime('%H:%M')}）"
                    )
                )

        except:
            pass

        # 未來7天取票
        try:

            if show.get("取票日期"):

                pickup_date = parse_date(show["取票日期"])

                days = (pickup_date - today).days

                if (
                    1 <= days <= 7
                    and show.get("取票狀態", "未取票") == "未取票"
                ):

                    upcoming.append(
                        (
                            pickup_date,
                            f"{pickup_date.strftime('%m/%d')}　🎫 {show['演出名稱']}"
                        )
                    )

        except:
            pass

        # 未來7天演出
        try:

            show_date = parse_date(show["演出日期"])

            days = (show_date - today).days

            if 1 <= days <= 7:

                upcoming.append(
                    (
                        show_date,
                        f"{show_date.strftime('%m/%d')}　🎤 {show['演出名稱']}"
                    )
                )

        except:
            pass

    msg = (
        f"📅 今日重點（{today.strftime('%m/%d')}）\n\n"
    )

    if not ticket_today and not pickup_today and not show_today:

        msg += "🎉 今天沒有待辦事項\n"

    else:

        if ticket_today:

            msg += "━━━━━━━━━━━━\n"
            msg += f"🎟 今天要搶票（{len(ticket_today)}）\n\n"

            for show in ticket_today:

                ticket_time = parse_datetime(show["搶票時間"])

                msg += (
                    f"🎤 {show['演出名稱']}\n"
                    f"🕛 {ticket_time.strftime('%H:%M')}\n"
                    f"💰 {format_price(show['價格張數'])}\n"
                    f"🌐 {show['售票平台']}\n\n"
                )

        if pickup_today:

            msg += "━━━━━━━━━━━━\n"
            msg += f"🎫 今天可取票（{len(pickup_today)}）\n\n"

            for show in pickup_today:

                msg += (
                    f"🎤 {show['演出名稱']}\n"
                )

            msg += "\n"

        if show_today:

            msg += "━━━━━━━━━━━━\n"
            msg += f"🎤 今天演出（{len(show_today)}）\n\n"

            for show in show_today:

                msg += (
                    f"🎤 {show['演出名稱']}\n"
                )

        # 未來7天
        upcoming.sort(key=lambda x: x[0])

        if upcoming:

            if ticket_today or pickup_today or show_today:
                msg += "\n━━━━━━━━━━━━\n\n"

            msg += "📆 未來 7 天\n\n"

            current_date = None

            for date, item in upcoming:

                if date != current_date:

                    current_date = date

                    msg += f"📅 {date.strftime('%m/%d')}\n"

                msg += item[6:] + "\n"

            msg += "\n"


    line_bot_api.push_message(
        GROUP_ID,
        TextSendMessage(text=msg)
    )

def clean_finished_shows():

    print("檢查過期演出")

    now = datetime.now() + timedelta(hours=8)

    shows = load_data()

    keep_shows = []

    for show in shows:

        try:

            last_show_date = parse_date(
                get_last_show_date(show)
            )

            delete_date = (
                last_show_date +
                timedelta(days=3)
            )

            if now.date() <= delete_date.date():

                keep_shows.append(show)

            else:

                print(
                    f"🗑️ 已自動清除：{show['演出名稱']}"
                )


        except Exception as e:

            print(
                "清除錯誤：",
                e
            )

            keep_shows.append(show)


    if len(keep_shows) != len(shows):

        # 刪除 Supabase 資料
        old_ids = [
            show["id"]
            for show in shows
            if show not in keep_shows
        ]

        for show_id in old_ids:

            try:

                supabase.table("shows") \
                    .delete() \
                    .eq("id", show_id) \
                    .execute()

                print(f"已刪除：{show_id}")

            except Exception as e:

                print(f"刪除失敗：{show_id}", e)
        

    print("清除完成")