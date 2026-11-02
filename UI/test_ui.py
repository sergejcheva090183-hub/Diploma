import uuid

import pytest
import requests
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pages.company_page import CompanyPage
from pages.login_page import LoginPage
from pages.chats_page import ChatsPage


def find_chat_via_api(api_key: str, base_url: str, title: str) -> dict | None:
    """Поиск группового чата по названию через API."""
    response = requests.get(
        url=f"{base_url}/group-chats",
        params={"title": title},
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30,
    )
    response.raise_for_status()
    for chat in response.json().get("content", []):
        if chat.get("title") == title:
            return chat
    return None


def get_user_id(api_key: str, base_url: str, email: str) -> str:
    """Получение ID пользователя по email через API."""
    response = requests.get(
        url=f"{base_url}/users",
        params={"email": email},
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30,
    )
    response.raise_for_status()
    for user in response.json().get("content", []):
        if user.get("email") == email:
            return user["id"]
    raise AssertionError(f"Сотрудник {email} не найден через API")


@pytest.mark.positive
def test_login(driver: WebDriver, ui_url: str, credentials: tuple[str, str]) -> None:
    """Авторизация в системе."""
    email, password = credentials
    page = LoginPage(driver)
    page.open(ui_url)
    page.login(email, password)
    assert page.is_logged_in(), "После входа форма авторизации осталась на экране"


@pytest.mark.positive
def test_create_department(logged_in_driver: WebDriver) -> None:
    """Создание отдела и проверка его появления в списке."""
    title = f"Отдел маркетинга {uuid.uuid4().hex[:6]}"
    page = CompanyPage(logged_in_driver)
    page.open_employees_section()
    page.add_department(title)
    assert page.is_department_in_list(title), f"Отдел «{title}» не появился"


@pytest.mark.positive
def test_add_employee_to_second_department(
        two_departments: tuple[str, str],
        logged_in_driver: WebDriver,
        employee_email: str,
) -> None:
    """Добавление одного сотрудника в два разных отдела."""
    first_department, second_department = two_departments
    page = CompanyPage(logged_in_driver)
    page.open_employees_section()
    page.add_employee_to_department(first_department, employee_email)
    page.add_employee_to_department(second_department, employee_email)
    page.open_employee_profile(employee_email)
    assert page.is_department_checked_in_profile(first_department), f"Не отмечен «{first_department}»"
    assert page.is_department_checked_in_profile(second_department), f"Не отмечен «{second_department}»"


@pytest.mark.positive
def test_create_group_chat(
        logged_in_driver: WebDriver,
        employee_email: str,
        api_key: str,
        base_url: str,
) -> """Создание группового чата и проверка через API.""":
    chat_name = f"Обсуждение релиза {uuid.uuid4().hex[:6]}"
    page = ChatsPage(logged_in_driver)

    page.open_messenger()
    page.open_create_group_chat_dialog()
    page.fill_chat_name(chat_name)
    page.select_employee(employee_email)
    page.click_create()

    # 1. Ждем, пока окно создания чата закроется (стабильность UI)
    WebDriverWait(logged_in_driver, 25).until(
        EC.invisibility_of_element_located(page.CREATE_CHAT_DIALOG),
        message="Диалоговое окно создания чата не закрыто"
    )

    # 2. Проверяем создание чата через API
    chat = WebDriverWait(logged_in_driver, 25, poll_frequency=1).until(
        lambda _: find_chat_via_api(api_key, base_url, chat_name),
        message=f"Чат «{chat_name}» не найден через API",
    )

    manager_id = get_user_id(api_key, base_url, employee_email)

    # Исправленная проверка: ищем в списке ID пользователей
    # Предполагаем, что chat['users'] — это список объектов {'id': '...', ...}
    user_ids = [user.get("id") for user in chat.get("users", [])]
    assert manager_id in user_ids, f"Сотрудник {employee_email} не добавлен в чат"


@pytest.mark.positive
def test_send_message_with_mention(
        logged_in_driver: WebDriver,
        api_group_chat: str,
        employee_email: str,
) -> None:
    """Отправка сообщения с упоминанием пользователя."""
    page = ChatsPage(logged_in_driver)
    page.open_messenger()
    page.open_chat(api_group_chat)
    page.send_message_with_mention(employee_email)
    assert page.is_message_sent_with_mention(employee_email), f"Сообщение с упоминанием {employee_email} не появилось"


@pytest.mark.positive
@pytest.mark.invite_user
def test_invite_employee_by_email(logged_in_driver: WebDriver) -> None:
    """
    Приглашение нового сотрудника в компанию по email.
    """
    unique_email = f"test.user_{uuid.uuid4().hex[:8]}@example.com"

    page = CompanyPage(logged_in_driver)
    page.open_employees_section()
    page.click_invite_employee_button()
    page.invite_employee_by_email(unique_email)

    assert page.is_invitation_in_list(unique_email), (
        f"Приглашение для {unique_email} не появилось в списке"
    )
    assert page.get_invitation_status(unique_email) == "Отправлено", (
        f"Статус приглашения для {unique_email} не 'Отправлено'"
    )