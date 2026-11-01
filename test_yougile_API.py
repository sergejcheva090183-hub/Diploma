import uuid
import requests
import pytest
from conftest import allure, ALLURE_AVAILABLE


# 2. Вспомогательная фикстура для логирования API
@pytest.fixture(scope="session")
def allure_api_tracker():
    """
    Предоставляет контекстный менеджер для логирования HTTP-запросов в Allure.
    """

    def _track_request(method: str, url: str, **kwargs):
        headers = kwargs.get("headers", {})
        safe_headers = {
            k: ("[MASKED]" if k.lower() == "authorization" else v)
            for k, v in headers.items()
        }

        step_name = f"{method.upper()} {url}"
        if "json" in kwargs:
            step_name += f" | Payload: {kwargs['json']}"

        return allure.step(step_name)

    return _track_request


# ПОЗИТИВНЫЕ ТЕСТЫ

@allure.title("Создание отдела: проверка генерации ID и сохранения данных")
@allure.story("Управление структурой: Департаменты")
@pytest.mark.positive
def test_create_department(api_key, base_url, allure_api_tracker):
    """
    Позитивный сценарий: Создание отдела.
    Проверяет генерацию ID и сохранение названия через GET.
    """
    with allure.step("Подготовка данных: генерация уникального названия отдела"):
        department_title = f"Автотест Отдел {uuid.uuid4()}"

    payload = {
        "title": department_title,
        "parentId": None,
        "users": {},
    }

    with allure.step("Выполнение запроса: создание отдела через POST"):
        with allure_api_tracker(
            "POST",
            f"{base_url}/departments",
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"},
        ):
            response = requests.post(
                url=f"{base_url}/departments",
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"},
            )

    with allure.step("Валидация ответа: проверка статуса 201 Created"):
        assert response.status_code == 201, (
            f"Статус {response.status_code}, а должен быть 201 Created."
        )

    with allure.step("Логирование ответа сервера"):
        if ALLURE_AVAILABLE:
            allure.attach(
                response.text,
                name="Ответ API (Create Dept)",
                attachment_type=allure.attachment_type.TEXT,
            )

    with allure.step("Валидация структуры: проверка наличия ID в теле ответа"):
        response_json = response.json()
        assert "id" in response_json, "В ответе на POST отсутствует ID созданного отдела"
        department_id = response_json["id"]

    with allure.step("Проверка сохранения данных: получение отдела через GET"):
        with allure_api_tracker(
            "GET",
            f"{base_url}/departments/{department_id}",
            headers={"Authorization": f"Bearer {api_key}"},
        ):
            get_response = requests.get(
                url=f"{base_url}/departments/{department_id}",
                headers={"Authorization": f"Bearer {api_key}"},
            )

    with allure.step("Валидация GET-запроса: проверка статуса 200 OK"):
        assert get_response.status_code == 200, (
            f"Не удалось получить отдел по ID. Статус: {get_response.status_code}. "
            f"Тело: {get_response.text}"
        )

    with allure.step("Валидация данных: проверка совпадения названия"):
        get_json = get_response.json()
        assert get_json.get("title") == department_title, (
            f"Название не совпадает. Ожидалось: '{department_title}', "
            f"Получено: '{get_json.get('title')}'"
        )


@allure.title("Получение списка сотрудников: проверка структуры и наполнения")
@allure.story("Управление персоналом: Сотрудники")
@pytest.mark.positive
def test_get_employees_list(api_key, base_url, allure_api_tracker):
    """
    Позитивный сценарий: Получение списка сотрудников.
    """
    url = f"{base_url}/users"

    with allure.step("Выполнение запроса: получение списка пользователей"):
        with allure_api_tracker(
            "GET", url, headers={"Authorization": f"Bearer {api_key}"}
        ):
            response = requests.get(
                url=url, headers={"Authorization": f"Bearer {api_key}"}
            )

    with allure.step("Валидация статуса: ожидание 200 OK"):
        assert response.status_code == 200, (
            f"Ожидался статус 200 OK, получен {response.status_code}. "
            f"Тело: {response.text}"
        )

    with allure.step("Валидация заголовков: проверка Content-Type"):
        content_type = response.headers.get("Content-Type", "")
        assert "application/json" in content_type, (
            f"Ожидался JSON, получен тип контента: {content_type}"
        )

    with allure.step("Валидация структуры: проверка корневых ключей (paging, content)"):
        response_json = response.json()
        assert isinstance(response_json, dict), (
            f"Ожидался объект (dict), получен {type(response_json)}"
        )
        assert "paging" in response_json, "В ответе отсутствует объект 'paging'"
        assert "content" in response_json, "В ответе отсутствует массив 'content'"

    with allure.step("Валидация данных: проверка, что список сотрудников не пуст"):
        employees = response_json["content"]
        assert isinstance(employees, list), (
            f"Поле 'content' должно быть списком, получен {type(employees)}"
        )
        assert len(employees) > 0, "Список сотрудников пуст"


@allure.title("Создание группового чата: проверка ID, названия и структуры ролей")
@allure.story("Коммуникации: Групповые чаты")
@pytest.mark.positive
def test_create_group_chat(api_key: str, base_url: str, allure_api_tracker):
    """
    Позитивный сценарий: Создание группового чата.
    """
    with allure.step("Подготовка данных: генерация уникального названия чата"):
        chat_title = f"Автотест Чат {uuid.uuid4()}"

    payload = {
        "title": chat_title,
        "users": {
            "e240d208-4618-4336-b788-77f11310647a": {"notified": True},
            "25218420-e66d-4395-ae37-a141c4e59eb2": {"notified": False},
        },
        "userRoleMap": {
            "e240d208-4618-4336-b788-77f11310647a": "admin",
            "25218420-e66d-4395-ae37-a141c4e59eb2": "user",
        },
        "roleConfigMap": {
            "admin": {
                "editProperties": True,
                "editAdmins": True,
                "editUsers": True,
                "sendMessages": True,
                "removeMessages": True,
            },
            "user": {
                "editProperties": False,
                "editAdmins": False,
                "editUsers": True,
                "sendMessages": True,
                "removeMessages": False,
            },
        },
    }

    with allure.step("Выполнение запроса: создание чата через POST"):
        with allure_api_tracker(
            "POST",
            f"{base_url}/group-chats",
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"},
        ):
            response = requests.post(
                url=f"{base_url}/group-chats",
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"},
            )

    with allure.step("Логирование ответа сервера"):
        print(f"\nСтатус: {response.status_code}")
        if ALLURE_AVAILABLE:
            try:
                allure.attach(
                    str(response.json()),
                    name="Ответ API (Create Chat)",
                    attachment_type=allure.attachment_type.JSON,
                )
            except Exception:
                allure.attach(
                    response.text,
                    name="Ответ API (Create Chat - Text)",
                    attachment_type=allure.attachment_type.TEXT,
                )

    with allure.step("Валидация статуса: ожидание 201 Created"):
        assert response.status_code == 201, (
            f"Статус {response.status_code}, а должен быть 201 Created."
        )

    with allure.step("Валидация данных: проверка наличия идентификатора"):
        data = response.json()
        assert isinstance(data.get("id"), str), "Не создан идентификатор."


# НЕГАТИВНЫЕ ПРОВЕРКИ

@allure.title("Создание отдела: негативная проверка отсутствия названия")
@allure.story("Управление структурой: Валидация данных")
@pytest.mark.negative
def test_create_department_without_title(api_key: str, base_url: str, allure_api_tracker):
    """
    Негативный сценарий: Создание отдела без заголовка.
    """
    payload = {"title": ""}

    with allure.step("Выполнение запроса: попытка создания отдела с пустым title"):
        with allure_api_tracker(
            "POST",
            f"{base_url}/departments",
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"},
        ):
            response = requests.post(
                url=f"{base_url}/departments",
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"},
            )

    with allure.step("Валидация статуса: ожидание 400 Bad Request"):
        assert response.status_code == 400, (
            f"Ожидался статус 400 Bad Request, но получен {response.status_code}."
        )

    with allure.step("Валидация структуры ошибки: проверка поля message"):
        data = response.json()
        if ALLURE_AVAILABLE:
            allure.attach(
                str(data), name="Ответ API (Error Dept)", attachment_type=allure.attachment_type.JSON
            )
        assert "message" in data and isinstance(data["message"], list), (
            "В ответе отсутствует поле 'message' в виде списка."
        )

    with allure.step("Валидация текста ошибки: проверка упоминания поля title"):
        error_text = " ".join(data.get("message", [])).lower()
        assert "title" in error_text, (
            f"Текст ошибки не содержит упоминания поля 'title'. Весь текст: {error_text}"
        )
        assert "empty" in error_text or "should not be empty" in error_text, (
            f"Текст ошибки не указывает на пустое значение. Весь текст: {error_text}"
        )


@allure.title("Удаление пользователя: запрет на удаление последнего администратора")
@allure.story("Управление персоналом: Целостность данных")
@pytest.mark.negative
def test_delete_company_owner_prohibited(api_key: str, base_url: str, allure_api_tracker):
    """
    Негативный сценарий: Попытка удалить владельца компании.
    """
    company_owner_id = "e240d208-4618-4336-b788-77f11310647a"

    with allure.step("Выполнение запроса: попытка удаления владельца"):
        with allure_api_tracker(
            "DELETE",
            f"{base_url}/users/{company_owner_id}",
            headers={"Authorization": f"Bearer {api_key}"},
        ):
            delete_response = requests.delete(
                url=f"{base_url}/users/{company_owner_id}",
                headers={"Authorization": f"Bearer {api_key}"},
            )

    with allure.step("Валидация статуса: ожидание 400 Bad Request"):
        assert delete_response.status_code == 400, (
            f"Ожидался статус 400 Bad Request, но получен {delete_response.status_code}."
        )

    with allure.step("Валидация текста ошибки: проверка запрета на удаление последнего админа"):
        try:
            response_data = delete_response.json()
        except ValueError:
            response_data = {}

        if ALLURE_AVAILABLE:
            allure.attach(
                str(response_data),
                name="Ответ API (Delete Owner)",
                attachment_type=allure.attachment_type.JSON,
            )

        assert "message" in response_data, "В ответе отсутствует поле 'message'."
        message_field = response_data.get("message")
        error_text = " ".join(
            message_field if isinstance(message_field, list) else [message_field]
        ).lower()

        assert "last admin" in error_text, (
            f"Текст ошибки не содержит упоминания 'last admin'. Весь текст: {error_text}"
        )
        assert "can’t remove last admin from company" in error_text, (
            f"Текст ошибки не содержит запрета на удаление. Весь текст: {error_text}"
        )

    with allure.step("Проверка целостности: пользователь-владелец все еще существует в системе"):
        with allure_api_tracker(
            "GET",
            f"{base_url}/users/{company_owner_id}",
            headers={"Authorization": f"Bearer {api_key}"},
        ):
            get_response = requests.get(
                url=f"{base_url}/users/{company_owner_id}",
                headers={"Authorization": f"Bearer {api_key}"},
            )
        assert get_response