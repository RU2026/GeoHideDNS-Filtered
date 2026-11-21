
import urllib.request
import re
import sys

SOURCE_URL = "https://raw.githubusercontent.com/Internet-Helper/GeoHideDNS/refs/heads/main/hosts/hosts"

TARGET_BLOCKS = [
    "# Supercell",
    "# Google Gemini AI",
    "# ChatGPT (OpenAI) AI",
    "# Claude AI",
]

def main():
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "GeoHideDNS-Filtered"}
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        source = response.read().decode("utf-8-sig")

    result = []
    found = set()
    capturing = False

    for line in source.splitlines():
        if re.match(r"^# [^#]", line):
            capturing = line in TARGET_BLOCKS
            if capturing:
                found.add(line)

        if capturing:
            result.append(line)

    missing = set(TARGET_BLOCKS) - found
    if missing:
        raise RuntimeError(f"Не найдены блоки: {missing}")

    with open("hosts.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(result).strip() + "\n")

    print("Успешно обновлено:", len(found), "блока")

if __name__ == "__main__":
    main()
