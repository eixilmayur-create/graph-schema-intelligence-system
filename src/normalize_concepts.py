import re
import unicodedata

def normalize_label(value: str | None) -> str:
    if value is None:
        return ""

    text = str(value).strip().lower()

    if not text:
        return ""

    text = unicodedata.normalize("NFKD", text)

    text = text.replace("&", " and ")

    text = re.sub(r"[^a-z0-9\s]", " ", text)

    text = re.sub(r"\s+", " ", text).strip()

    return text

if __name__ == "__main__":
    examples = [
        "Engineering",
        "ENG",
        "Data & Analytics",
        "H.R.",
        "  Product   Mgmt  ",
    ]

    for example in examples:
        print(example, "->", normalize_label(example))
