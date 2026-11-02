import os
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver

from pages.login_page import LoginPage
from contextlib import nullcontext

try:
    import allure
    ALLURE_AVAILABLE = True
except ImportError:
    class AllureStub:
        step = staticmethod(nullcontext)
        title = staticmethod(lambda x: None)
        attach = staticmethod(lambda *args, **kwargs: None)

    allure = AllureStub()
    ALLURE_AVAILABLE = False

load_dotenv()

DEFAULT_API_URL = "https://ru.yougile.com/api-v2"
DEFAULT_UI_URL = "https://ru.yougile.com"
INVALID_KEYS = {"", "your-real-x-api-key-here", "test-key", "null"}
SCREENSHOTS_DIR = Path("screenshots")


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> Iterator[None]:
    report = yield
    setattr(item, f"rep_{report.when}", report)
    return report


@pytest.fixture(scope="session")
def api_key() -> str:
    key = os.getenv("YOUGILE_API_KEY")
    if not key or key in INVALID_KEYS:
        pytest.exit("КРИТИЧЕСКАЯ ОШИБКА: YOUGILE_API_KEY не задан или является заглушкой.", returncode=1)
    return key


@pytest.fixture(scope="session")
def base_url() -> str:
    return os.getenv("YOUGILE_BASE_API_URL", DEFAULT_API_URL).rstrip("/")


@pytest.fixture(scope="session")
def ui_url() -> str:
    return os.getenv("YOUGILE_BASE_UI_URL", DEFAULT_UI_URL).rstrip("/")


@pytest.fixture(scope="session")
def credentials() -> tuple[str, str]:
    email = os.getenv("YOUGILE_EMAIL")
    password = os.getenv("YOUGILE_PASSWORD")
    if not email or not password:
        pytest.exit("КРИТИЧЕСКАЯ ОШИБКА: YOUGILE_EMAIL или YOUGILE_PASSWORD не заданы.", returncode=1)
    return email, password


@pytest.fixture(scope="session")
def employee_email() -> str:
    email = os.getenv("YOUGILE_TEST_EMPLOYEE")
    if not email:
        pytest.exit("КРИТИЧЕСКАЯ ОШИБКА: YOUGILE_TEST_EMPLOYEE не задан в .env.", returncode=1)
    return email


@pytest.fixture
def two_departments(api_key: str, base_url: str) -> tuple[str, str]:
    suffix = uuid.uuid4().hex[:6]
    titles = (f"Разработка {suffix}", f"Тестирование {suffix}")
    for title in titles:
        response = requests.post(
            url=f"{base_url}/departments",
            json={"title": title},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30,
        )
        assert response.status_code == 201, f"Не удалось создать отдел «{title}»: {response.status_code} {response.text}"
    return titles


@pytest.fixture
def driver(request: pytest.FixtureRequest) -> Iterator[WebDriver]:
    options = Options()
    if os.getenv("HEADLESS", "false").lower() == "true":
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    browser = webdriver.Chrome(options=options)
    yield browser

    failed = any(
        getattr(request.node, f"rep_{phase}", None) is not None
        and getattr(request.node, f"rep_{phase}").failed
        for phase in ("setup", "call")
    )
    if failed:
        SCREENSHOTS_DIR.mkdir(exist_ok=True)
        browser.save_screenshot(str(SCREENSHOTS_DIR / f"{request.node.name}.png"))
    browser.quit()


@pytest.fixture
def logged_in_driver(driver: WebDriver, ui_url: str, credentials: tuple[str, str]) -> WebDriver:
    email, password = credentials
    page = LoginPage(driver)
    page.open(ui_url)
    page.login(email, password)
    assert page.is_logged_in(), "Не удалось войти в систему"
    return driver


@pytest.fixture
def api_group_chat(api_key: str, base_url: str) -> str:
    headers = {"Authorization": f"Bearer {api_key}"}
    users_response = requests.get(url=f"{base_url}/users", headers=headers, timeout=30)
    users_response.raise_for_status()
    user_ids = [user["id"] for user in users_response.json()["content"]]

    title = f"Чат для упоминаний {uuid.uuid4().hex[:6]}"
    payload = {
        "title": title,
        "users": {user_id: {"notified": True} for user_id in user_ids},
        "userRoleMap": {user_id: "admin" for user_id in user_ids},
        "roleConfigMap": {
            "admin": {
                "editProperties": True,
                "editAdmins": True,
                "editUsers": True,
                "sendMessages": True,
                "removeMessages": True,
            }
        },
    }
    response = requests.post(
        url=f"{base_url}/group-chats",
        json=payload,
        headers=headers,
        timeout=30,
    )
    assert response.status_code == 201, f"Не удалось создать чат через API: {response.status_code} {response.text}"
    return title