# sync.py
"""
Синхронизация CRWO с сервером.
- Номер проверяется на сервере перед формированием заявки.
- Offline — заявка формируется без проверки (с предупреждением).
"""
import os
import uuid
import threading

from paths import service_path
from api_client import api


def get_device_id():
    """Уникальный ID устройства. Сохраняется в service/device_id.txt."""
    p = service_path('device_id.txt')
    if os.path.exists(p):
        try:
            with open(p) as f:
                did = f.read().strip()
                if did:
                    return did
        except Exception as e:
            print(f"[sync] read device_id error: {e}")

    did = uuid.uuid4().hex[:16]
    try:
        with open(p, 'w') as f:
            f.write(did)
    except Exception as e:
        print(f"[sync] write device_id error: {e}")

    print(f"[sync] new device_id = {did}")
    return did


def check_crwo_number(region, value, organization="Миранда-Медиа"):
    """
    Проверить номер на сервере в рамках организации.
    Возвращает:
      {"status": "free"}                                       — свободен
      {"status": "taken", "next_free": N, "used_by": "...", ...} — занят
      {"status": "offline", "reason": "..."}                   — нет связи
    """
    try:
        resp = api.post("/crwo/check", json={
            "region": region,
            "value": int(value),
            "organization": organization,
        }, timeout=5)

        if resp.status_code == 200:
            return resp.json()

        if resp.status_code == 401:
            return {"status": "offline", "reason": "unauthorized"}

        print(f"[crwo] check HTTP {resp.status_code}: {resp.text}")
        return {"status": "offline", "reason": f"http_{resp.status_code}"}

    except Exception as e:
        print(f"[crwo] check exception: {e}")
        return {"status": "offline", "reason": str(e)}


def commit_crwo_number(region, value, organization="Миранда-Медиа", forced=False):
    """
    Зафиксировать номер на сервере в рамках организации. Фоном.
    """
    def _push():
        try:
            resp = api.post("/crwo/commit", json={
                "region": region,
                "value": int(value),
                "organization": organization,
                "device_id": get_device_id(),
                "forced": bool(forced),
            }, timeout=10)

            if resp.status_code == 200:
                print(f"[crwo] committed {organization}/{region}-{value} forced={forced}")
            else:
                print(f"[crwo] commit HTTP {resp.status_code}: {resp.text}")

        except Exception as e:
            print(f"[crwo] commit exception: {e}")

    threading.Thread(target=_push, daemon=True).start()