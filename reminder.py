import config

from datetime import datetime, timedelta

from data import (
    supabase,
    load_data,
    update_show,
)

from utils import (
    parse_date,
    parse_datetime,
    get_last_show_date,
    split_show_dates,
)

from today_card import build_today_card

from reminder_card import (
    build_tomorrow_ticket_card,
    build_ticket_countdown_card,
    build_pickup_reminder_card,
    build_show_day_reminder_card,
)

# =====================
# 提醒功能
# =====================

def check_reminders():

    print("提醒檢查執行", datetime.now())

    now = datetime.now() + timedelta(hours=8)

    shows = load_data()

    for show in shows:

        reminder_defaults = {
            "前一天": False,
            "30分鐘": False,
            "10分鐘": False,
            "取票": False,
            "演出日": False,
        }

        if not isinstance(show.get("提醒"), dict):
            show["提醒"] = {}

        for reminder_key, default_value in reminder_defaults.items():
            show["提醒"].setdefault(
                reminder_key,
                default_value,
            )

        print(
            "提醒狀態：",
            f"{show.get('藝人', '')}｜"
            f"{show.get('活動', '')}｜"
            f"{show.get('活動名稱', '')}",
            show["提醒"],
        )


        show.setdefault("搶票狀態", "待搶票")
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
                remind_time <= now <= remind_time + timedelta(minutes=3)
                and not show["提醒"]["前一天"]
            ):

                try:

                    config.line_bot_api.push_message(
                        config.GROUP_ID,
                        build_tomorrow_ticket_card(show)
                    )

                except Exception as e:

                    print(
                        "前一天提醒推播失敗：",
                        repr(e),
                        flush=True,
                    )

                else:

                    show["提醒"]["前一天"] = True
                    update_show(show)


            diff = ticket_time - now

            print("=" * 50)
            print("現在時間：", now)
            print(
                "演出：",
                f"{show.get('藝人', '')}｜"
                f"{show.get('活動', '')}｜"
                f"{show.get('活動名稱', '')}",
            )
            print("搶票時間：", ticket_time)
            print("剩餘：", diff)
            print("30分鐘：", show["提醒"]["30分鐘"])
            print("10分鐘：", show["提醒"]["10分鐘"])


            # 前30分鐘

            if (
                timedelta(minutes=29)
                <= diff 
                < timedelta(minutes=31)
                and not show["提醒"]["30分鐘"]
            ):


                print(">>> 發送30分鐘提醒")


                try:

                    config.line_bot_api.push_message(
                        config.GROUP_ID,
                        build_ticket_countdown_card(
                            show=show,
                            minutes=30,
                        )
                    )

                except Exception as e:

                    print(
                        "30分鐘提醒推播失敗：",
                        repr(e),
                        flush=True,
                    )

                else:

                    show["提醒"]["30分鐘"] = True
                    update_show(show)


            # 前10分鐘

            if (
                timedelta(minutes=9)
                <= diff 
                < timedelta(minutes=11)
                and not show["提醒"]["10分鐘"]
            ):

                print(">>> 發送10分鐘提醒")


                try:

                    config.line_bot_api.push_message(
                        config.GROUP_ID,
                        build_ticket_countdown_card(
                            show=show,
                            minutes=10,
                        )
                    )

                except Exception as e:

                    print(
                        "10分鐘提醒推播失敗：",
                        repr(e),
                        flush=True,
                    )

                else:

                    show["提醒"]["10分鐘"] = True
                    update_show(show)


        except Exception as e:

            print(
                f"提醒錯誤：{e}"
            )


        # =====================
        # 取票提醒
        # =====================

        if show.get("取票日期"):

            try:

                pickup_time = parse_datetime(
                    f"{show['取票日期']} 13:00"
                )

                if pickup_time is None:
                    raise ValueError(
                        f"無法解析取票日期：{show['取票日期']}"
                    )

                if (
                    pickup_time
                    <= now
                    < pickup_time + timedelta(minutes=1)
                    and not show["提醒"]["取票"]
                    and show.get("搶票狀態") == "已搶票"
                ):

                   
                    try:

                        config.line_bot_api.push_message(
                            config.GROUP_ID,
                            build_pickup_reminder_card(show),
                        )

                        ticket_master = show.get("搶票大師", "").strip()
                        pickup_person = show.get("取票人", "").strip()

                        if pickup_person:

                            if ticket_master and ticket_master != pickup_person:

                                config.push_mention_message(
                                    config.GROUP_ID,
                                    "🎯 取票序號出來囉～ 🐱",
                                    [ticket_master],
                                )

                                config.push_mention_message(
                                    config.GROUP_ID,
                                    "👤 記得去取票～",
                                    [pickup_person],
                                )

                            else:

                                config.push_mention_message(
                                    config.GROUP_ID,
                                    "👤 記得去取票～",
                                    [pickup_person],
                                )

                    except Exception as error:

                        print(
                            "取票提醒推播失敗：",
                            repr(error),
                            flush=True,
                        )

                    else:

                        show["提醒"]["取票"] = True
                        update_show(show)

            except Exception as error:

                print(
                    "取票提醒處理錯誤：",
                    f"{show.get('藝人', '')}｜"
                    f"{show.get('活動', '')}｜"
                    f"{show.get('活動名稱', '')}",
                    repr(error),
                    flush=True,
                )

        # =====================
        # 演出日提醒
        # =====================

        try:

            show_dates = show.get(
                "演出日期",
                ""
            )

            date_values = split_show_dates(show_dates)

            is_show_day = False

            for date_value in date_values:

                parsed_show_date = parse_date(
                    date_value
                )

                if parsed_show_date is None:
                    continue

                if hasattr(
                    parsed_show_date,
                    "date",
                ):
                    parsed_date = (
                        parsed_show_date.date()
                    )
                else:
                    parsed_date = parsed_show_date

                if parsed_date == now.date():

                    is_show_day = True
                    break

            show_day_time = now.replace(
                hour=10,
                minute=0,
                second=0,
                microsecond=0,
            )

            if (
                is_show_day
                and show_day_time
                <= now
                < show_day_time + timedelta(minutes=1)
                and not show["提醒"]["演出日"]
            ):

                try:

                    config.line_bot_api.push_message(
                        config.GROUP_ID,
                        build_show_day_reminder_card(show)
                    )

                    show["提醒"]["演出日"] = True
                    update_show(show)


                    if (
                        show.get("搶票狀態") == "已搶票"
                        and show.get("取票狀態") != "已取票"
                    ):

                        ticket_master = show.get("搶票大師", "").strip()
                        pickup_person = show.get("取票人", "").strip()

                        if pickup_person:

                            if ticket_master and ticket_master != pickup_person:

                                config.push_mention_message(
                                    config.GROUP_ID,
                                    "🎯 如果還沒提供取票序號，記得提供唷～ 🐱",
                                    [ticket_master],
                                )

                                config.push_mention_message(
                                    config.GROUP_ID,
                                    "👤 如果還沒取票，記得去取票唷～",
                                    [pickup_person],
                                )

                            else:

                                config.push_mention_message(
                                    config.GROUP_ID,
                                    "👤 如果還沒取票，記得去取票唷～",
                                    [pickup_person],
                                )

                except Exception as e:

                    print(
                        "演出日提醒推播失敗：",
                        repr(e),
                        flush=True,
                    )


        except Exception as e:

            print(
                "演出日提醒錯誤：",
                repr(e),
                flush=True,
            )

# =====================
# 今日重點
# =====================

def send_today_summary():

    try:

        config.line_bot_api.push_message(
            config.GROUP_ID,
            build_today_card()
        )

        print("今日待辦卡片已推送")

    except Exception as e:

        print(
            "今日待辦卡片推播失敗：",
            repr(e),
            flush=True,
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
                    "🗑️ 已自動清除：",
                    f"{show.get('藝人', '')}｜"
                    f"{show.get('活動', '')}｜"
                    f"{show.get('活動名稱', '')}",
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

                print(
                    "刪除失敗：",
                    repr(e),
                    flush=True,
                )
        

    print("清除完成")