# test_api.py — быстрый тест api_client без запуска Kivy
from api_client import api, API_URL


def main():
    print(f"API_URL = {API_URL}")
    print(f"Авторизован: {api.is_authorized()}")
    print()

    # 1. Health
    print("── /health ──")
    r = api.get("/health")
    print(f"  status={r.status_code} body={r.text}")
    print()

    # 2. Регистрация
    print("── /auth/register ──")
    ok, detail = api.register("TestUser", "Testov", "test12345")
    print(f"  ok={ok} detail={detail!r}")
    print()

    # 3. Логин
    print("── /auth/login ──")
    data = api.login("TestUser", "Testov", "test12345")
    print(f"  data={data}")
    print(f"  is_authorized={api.is_authorized()}")
    print()

    # 4. /me
    print("── /auth/me ──")
    me = api.fetch_me()
    print(f"  me={me}")
    print()

    # 5. Выход
    print("── logout ──")
    api.clear_token()
    print(f"  is_authorized={api.is_authorized()}")


if __name__ == "__main__":
    main()