import re

print("價格原始值：", repr(value))
def format_price(value):

    if not value:
        return "未設定"

    text = str(value).strip()

    # 統一乘號
    text = text.replace("＊", "*").replace("x", "*").replace("X", "*")

    # 3800*2
    m = re.match(r"^(\d+)\*(\d+)$", text)
    if m:
        price = int(m.group(1))
        count = m.group(2)
        return f"${price:,} ×{count}"

    # VIP6800*2
    m = re.match(r"^(.*?)(\d+)\*(\d+)$", text)
    if m:
        prefix = m.group(1).strip()
        price = int(m.group(2))
        count = m.group(3)
        return f"{prefix} ${price:,} ×{count}"

    # 3800
    if text.isdigit():
        return f"${int(text):,}"

    # $3800
    if text.startswith("$") and text[1:].isdigit():
        return f"${int(text[1:]):,}"

    return text
