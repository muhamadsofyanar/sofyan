import re

def parse_finance(text: str):
    text = text.lower()
    number = re.search(r'(\\d+)', text)
    if not number:
        return None

    amount = int(number.group(1))

    if "keluar" in text:
        kind = "expense"
    elif "masuk" in text:
        kind = "income"
    else:
        return None

    return {
        "type": kind,
        "amount": amount,
        "raw_text": text
    }