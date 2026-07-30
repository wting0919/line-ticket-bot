from datetime import datetime, timedelta
import re   # 如果 split_show_dates 有用到 regex


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

    text = re.sub(
        r"(.*?\$?)?(\d[\d,]*)\*(\d+)",
        repl,
        text
    )

    return text


WEEKDAY = ["一", "二", "三", "四", "五", "六", "日"]

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

def split_show_dates(value):

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

        # 只有日期，例如 11
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

        print("日期解析錯誤：", value, e)

        return datetime.max
