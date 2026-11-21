
import urllib.request
import re
import sys
import ipaddress

SOURCE_URL = (
    "https://raw.githubusercontent.com/"
    "Internet-Helper/GeoHideDNS/refs/heads/main/hosts/hosts"
)

TARGET_BLOCKS = [
    "# Supercell",
    "# Google Gemini AI",
    "# ChatGPT (OpenAI) AI",
    "# Claude AI",
]

def main():
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "GeoHideDNS-Filtered/1.0"}
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        source = response.read().decode("utf-8-sig")

    hosts_result = []
    rules_result = []
    found = set()
    seen_rules = set()
    capturing = False

    for line in source.splitlines():

        # Определяем границы блоков
        if re.match(r"^# [^#]", line):
            capturing = line in TARGET_BLOCKS

            if capturing:
                found.add(line)

                if hosts_result and hosts_result[-1] != "":
                    hosts_result.append("")

                rules_result.append("")
                rules_result.append("! " + line)

        if not capturing:
            continue

        hosts_result.append(line)

        # Пропускаем комментарии и пустые строки
        clean_line = line.split("#", 1)[0].strip()

        if not clean_line:
            continue

        parts = clean_line.split()

        if len(parts) < 2:
            continue

        ip = parts[0]

        try:
            ipaddress.ip_address(ip)
        except ValueError:
            continue

        # Один IP может соответствовать нескольким доменам
        for domain in parts[1:]:

            if domain.startswith("#"):
                break

            rule = f"||{domain}^$dnsrewrite={ip}"

            if rule not in seen_rules:
                rules_result.append(rule)
                seen_rules.add(rule)

    missing = set(TARGET_BLOCKS) - found

    if missing:
        raise RuntimeError(
            "Не найдены блоки: " + ", ".join(sorted(missing))
        )

    with open("hosts.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(hosts_result).strip() + "\n")

    with open("adguard-rules.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(rules_result).strip() + "\n")

    print("Успешно!")
    print("Найдено блоков:", len(found))
    print("Создано правил:", len(seen_rules))
    print("Созданы hosts.txt и adguard-rules.txt")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("Ошибка:", error)
        sys.exit(1)
