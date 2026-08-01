from datetime import datetime, timedelta
import re

# =====================
# 價格
# =====================

def format_price(value):

    if not value:
        return "未設定"

    text = str(value).strip()
    text = text.replace("＊", "*").replace("x", "*").replace("X", "*")

    def repl(match):
        prefix = match.group(1) or ""
        price = match.group(2).replace(",", "")
        count = match.group(3)

        return f"{prefix}${int(price):,} ×{count}"

    return re.sub(
        r"(.*?\$?)?(\d[\d,]*)\*(\d+)",
        repl,
        text
    )


# =====================
# 日期
# =====================

WEEKDAY = ["一", "二", "三", "四", "五", "六", "日"]


def parse_date(value):

    if not value:
        return datetime.max

    try:

        # Supabase ISO
        if "T" in value:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            ).replace(tzinfo=None)

        # 2026-08-17
        if "-" in value:
            return datetime.strptime(
                value,
                "%Y-%m-%d"
            )

        # 2026/08/17
        return datetime.strptime(
            value,
            "%Y/%m/%d"
        )

    except Exception as e:

        print(
            "日期解析錯誤：",
            value,
            repr(e),
            flush=True,
        )

        return datetime.max


def split_show_dates(value):

    if not value:
        return []

    value = value.strip().replace("，", "、").replace("-", "/")

    # 10/10~10/12
    if "~" in value:

        start, end = value.split("~")

        start = normalize_show_date(start)
        end = normalize_show_date(end)

        start_date = parse_date(start)
        end_date = parse_date(end)

        result = []

        while start_date <= end_date:

            result.append(
                start_date.strftime("%Y/%m/%d")
            )

            start_date += timedelta(days=1)

        return result

    result = []

    year = datetime.now().year
    last_month = None

    for item in value.split("、"):

        item = item.strip()

        if "/" not in item:
            item = f"{last_month}/{item}"

        if item.count("/") == 1:

            month = item.split("/")[0]
            last_month = month
            item = f"{year}/{item}"

        result.append(
            datetime.strptime(
                item,
                "%Y/%m/%d"
            ).strftime("%Y/%m/%d")
        )

    return result


def normalize_show_date(value):

    return "、".join(
        split_show_dates(value)
    )


def get_first_show_date(show):

    dates = split_show_dates(
        show.get("演出日期", "")
    )

    return dates[0] if dates else ""


def get_last_show_date(show):

    dates = split_show_dates(
        show.get("演出日期", "")
    )

    return dates[-1] if dates else ""


def format_show_dates(value):

    if not value:
        return ""

    result = []

    for d in split_show_dates(value):

        dt = parse_date(d)

        result.append(
            f"{dt.strftime('%Y/%m/%d')}（{WEEKDAY[dt.weekday()]}）"
        )

    return "\n".join(result)


def format_show_dates_inline(value):

    return format_show_dates(value).replace("\n", "、")

# =====================
# 時間
# =====================

def parse_datetime(value):

    if not value:
        return datetime.max

    try:

        # Supabase ISO
        if "T" in value:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            ).replace(tzinfo=None)

        # 2026-08-17 12:00
        if "-" in value:
            return datetime.strptime(
                value,
                "%Y-%m-%d %H:%M"
            )

        # 2026/08/17 12:00
        return datetime.strptime(
            value,
            "%Y/%m/%d %H:%M"
        )

    except Exception as e:

        print(
            "時間解析錯誤：",
            value,
            repr(e),
            flush=True,
        )

        return datetime.max


def format_datetime(value):

    dt = parse_datetime(value)

    if dt == datetime.max:
        return value

    return dt.strftime("%Y/%m/%d %H:%M")


def format_date(value):

    dt = parse_date(value)

    if dt == datetime.max:
        return str(value).replace("-", "/")

    return dt.strftime("%Y/%m/%d")


# =====================
# 取票
# =====================

def normalize_ticket_time(value):

    value = value.strip().replace("-", "/")
    date_part, time_part = value.split(" ", 1)

    if date_part.count("/") == 1:
        date_part = f"{datetime.now().year}/{date_part}"

    result = datetime.strptime(
        f"{date_part} {time_part}",
        "%Y/%m/%d %H:%M"
    )

    return result.strftime("%Y/%m/%d %H:%M")


def normalize_pickup_date(value, show_date):

    value = value.strip().replace("-", "/")

    if value == "略過":
        return ""

    if value.endswith("天前"):

        days = int(
            value.replace("天前", "").strip()
        )

        event_date = parse_date(
            split_show_dates(show_date)[0]
        )

        return (
            event_date - timedelta(days=days)
        ).strftime("%Y/%m/%d")

    return normalize_show_date(value)


# =====================
# 排序
# =====================

def sort_shows(shows):
    # 搶票時間排序

    return sorted(
        shows,
        key=lambda x: parse_datetime(
            x.get("搶票時間")
        )
    )



def sort_by_show_date(shows):
    # 演出日期排序

    return sorted(
        shows,
        key=lambda show: parse_date(
            get_first_show_date(show)
        )
    )


def sort_by_pickup_date(shows):
    # 取票日期排序

    return sorted(
        shows,
        key=lambda x: (
            parse_date(x.get("取票日期")),
            parse_datetime(x.get("搶票時間")),
            str(x.get("id", ""))
        )
    )

def format_ticket_status(status):

    return {
        "等待搶票": "🟡 等待搶票",
        "已搶票": "✅ 已搶票",
        "未搶到": "❌ 未搶到",
    }.get(
        status,
        "🟡 等待搶票"
    )

def format_pickup_status(show):

    if show.get("搶票狀態") != "已搶票":
        return ""

    return (
        "✅ 已取票"
        if show.get("取票狀態") == "已取票"
        else "❗ 未取票"
    )

# =====================
# 共用文字
# =====================

LIST_FOOTER = (
    "\n──────────\n"
    "👆 請使用下方按鈕查看詳細資料"
)