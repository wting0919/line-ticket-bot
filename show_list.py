from data import (
    load_data,
)

from utils import (
    sort_shows,
    sort_by_show_date,
    sort_by_pickup_date,
)

# =====================
# 共用列表功能
# =====================

def get_waiting_shows():

    shows = sort_shows(load_data())

    waiting_shows = []

    for show in shows:

        show.setdefault(
            "搶票狀態",
            "待搶票"
        )

        if show["搶票狀態"] == "待搶票":

            waiting.append(show)

    return waiting


def get_pickup_shows():

    shows = sort_by_pickup_date(load_data())

    pickup_shows = []

    for show in shows:

        show.setdefault(
            "取票狀態",
            "未取票"
        )

        show.setdefault(
            "搶票狀態",
            "待搶票"
        )

        if (
            show.get("取票日期")
            and show["取票狀態"] == "未取票"
            and show.get("搶票狀態") == "已搶票"
        ):

            pickup.append(show)

    return pickup


def get_all_shows():

    shows = sort_by_show_date(load_data())

    return shows