import re

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