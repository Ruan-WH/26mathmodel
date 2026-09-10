import html
import json
import re
import sys
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[2] / "tmp" / "shared_chat" / "reference.html"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    raw = SOURCE.read_text(encoding="utf-8")
    payloads = re.findall(r"streamController\.enqueue\((\"(?:\\.|[^\"\\])*\")\)", raw)
    candidates: list[str] = []
    for quoted in payloads:
        decoded = json.loads(quoted)
        try:
            values = json.loads(decoded)
        except json.JSONDecodeError:
            continue
        for value in values:
            if isinstance(value, str) and len(value) > 200:
                candidates.append(html.unescape(value))
    candidates.sort(key=len, reverse=True)
    for index, value in enumerate(candidates[:5], start=1):
        print(f"\n=== CANDIDATE {index} ({len(value)} chars) ===\n")
        print(value)


if __name__ == "__main__":
    main()
