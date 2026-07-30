from datetime import datetime, timedelta

from data import (
    load_data,
)

from utils import (
    parse_datetime,
    sort_shows,
    sort_by_show_date,
    sort_by_pickup_date,
)

# =====================
# 共用列表功能
# =====================

def get_waiting_shows():

    shows = sort_shows(load_data())

    waiting = []

    now = datetime.now() + timedelta(hours=8)

    for show in shows:

        show.setdefault(
            "搶票狀態",
            "等待搶票"
        )

        if show["搶票狀態"] == "等待搶票":

            try:

                ticket_time = parse_datetime(
                    show["搶票時間"]
                )

                if ticket_time > now:
                    waiting.append(show)

            except Exception as e:

                print(
                    "搶票時間錯誤：",
                    e
                )

    return waiting


def get_pickup_shows():

    shows = sort_by_pickup_date(load_data())

    pickup = []

    for show in shows:

        show.setdefault(
            "取票狀態",
            "未取票"
        )

        if (
            show.get("取票日期")
            and show["取票狀態"] == "未取票"
        ):

            pickup.append(show)


    return pickup


def get_all_shows():

    shows = sort_by_show_date(load_data())

    print("演出列表讀取：", shows)

    return shows
