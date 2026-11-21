
import os
import json
import urllib.request
import urllib.error

API = "https://api.adguard-dns.io"
START = "! BEGIN GEOFILTER AUTO"
END = "! END GEOFILTER AUTO"


def api_request(path, method="GET", data=None):
    key = os.environ["ADGUARD_API_KEY"]

    headers = {
        "Authorization": f"ApiKey {key}",
        "Accept": "application/json",
    }

    body = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")

    request = urllib.request.Request(
        API + path,
        data=body,
        headers=headers,
        method=method
    )

    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            content = response.read()
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"AdGuard API HTTP {error.code}: {details}"
        )


def get_server_id():
    server_id = os.getenv("ADGUARD_DNS_SERVER_ID")

    if server_id:
        return server_id

    result = api_request("/oapi/v2/dns_servers?limit=100")
    servers = result.get("items", [])

    if not servers:
        raise RuntimeError("DNS-серверы не найдены")

    defaults = [s for s in servers if s.get("default")]

    if len(defaults) == 1:
        selected = defaults[0]
    elif len(servers) == 1:
        selected = servers[0]
    else:
        raise RuntimeError(
            "Найдено несколько серверов. "
            "Добавь ADGUARD_DNS_SERVER_ID в GitHub Variables."
        )

    print("Выбран сервер:", selected.get("name"))
    return selected["id"]


def main():
    if not os.getenv("ADGUARD_API_KEY"):
        raise RuntimeError("Не задан ADGUARD_API_KEY")

    with open("adguard-rules.txt", encoding="utf-8") as file:
        new_rules = list(dict.fromkeys(
            line.strip()
            for line in file
            if line.strip()
        ))

    if not new_rules:
        raise RuntimeError("Список правил пустой. Обновление отменено.")

    server_id = get_server_id()
    path = f"/oapi/v1/dns_servers/{server_id}/settings"

    settings = api_request(path)
    user_settings = settings.get("user_rules_settings", {})
    old_rules = user_settings.get("rules", [])

    # Сохраняем правила, которые не принадлежат этому скрипту
    preserved = []
    inside = False

    for rule in old_rules:
        if rule == START:
            if inside:
                raise RuntimeError("Обнаружен повторный маркер начала")
            inside = True
            continue

        if rule == END:
            if not inside:
                raise RuntimeError("Обнаружен маркер конца без начала")
            inside = False
            continue

        if not inside:
            preserved.append(rule)

    if inside:
        raise RuntimeError("Не найден конец автоматического блока")

    final_rules = preserved + [START] + new_rules + [END]

    payload = {
        "user_rules_settings": {
            "enabled": True,
            "rules": final_rules
        }
    }

    api_request(path, method="PUT", data=payload)

    print("Синхронизация завершена!")
    print("Новых правил:", len(new_rules))
    print("Сохранено остальных правил:", len(preserved))


if __name__ == "__main__":
    main()
