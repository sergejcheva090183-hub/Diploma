import os
import uuid
import pytest
import requests
from dotenv import load_dotenv

load_dotenv()

# 1. Единый блок условного импорта Allure
try:
    import allure

    ALLURE_AVAILABLE = True
except ImportError:
    class _DummyAllure:
        @staticmethod
        def step(name):
            class _DummyContext:
                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    pass

            return _DummyContext()

        @staticmethod
        def attach(body=None, name=None, attachment_type=None):
            pass

        @staticmethod
        def title(name):
            def decorator(func):
                return func

            return decorator

        @staticmethod
        def story(name):
            def decorator(func):
                return func

            return decorator


    allure = _DummyAllure()
    ALLURE_AVAILABLE = False


# 2. Фикстура для выполнения HTTP-запросов с логированием в Allure
@pytest.fixture(scope="session")
def allure_api_tracker():
    """
    Выполняет HTTP-запрос через requests, логирует его в Allure и прикрепляет ответ.
    Автоматически добавляет Bearer-токен в заголовки.
    """

    def _perform_request(method: str, url: str, api_key: str, **kwargs):
        # Копируем заголовки, чтобы избежать мутации входных данных
        headers = kwargs.get('headers', {}).copy()
        if 'Authorization' not in headers:
            headers['Authorization'] = f"Bearer {api_key}"
        kwargs['headers'] = headers

        # Формируем название шага
        step_name = f"{method.upper()} {url}"
        if 'json' in kwargs:
            step_name += f" | Payload: {kwargs['json']}"

        with allure.step(step_name):
            response = requests.request(method, url, **kwargs)

            if ALLURE_AVAILABLE:
                status_label = "SUCCESS" if response.status_code < 400 else "FAILURE"

                # Текстовый ответ
                allure.attach(
                    body=response.text,
                    name=f"Ответ [{status_label}] {response.status_code}",
                    attachment_type=allure.attachment_type.TEXT
                )

                # Попытка прикрепить JSON
                try:
                    json_body = response.json()
                    allure.attach(
                        body=str(json_body),
                        name=f"Ответ JSON [{status_label}]",
                        attachment_type=allure.attachment_type.JSON
                    )
                except ValueError:
                    pass  # Ответ не в формате JSON

            return response

    return _perform_request


# 3. Фикстура-валидатор статус-кодов (для сокращения кода в тестах)
@pytest.fixture(scope="session")
def assert_status():
    def _assert(response, expected_code):
        assert response.status_code == expected_code, \
            f"Ожидался статус {expected_code}, получен {response.status_code}. Тело: {response.text}"

    return _assert


# 4. Вспомогательная фикстура для трекинга переменных окружения
@pytest.fixture(scope="session")
def allure_env_tracker():
    def _track_getenv(var_name, default_value=None):
        step_name = f"Получение переменной окружения: {var_name}"
        if default_value is not None:
            step_name += f" (по умолчанию: {default_value})"
        return allure.step(step_name)

    return _track_getenv


# 5. Фикстура API-ключа
@pytest.fixture(scope="session")
def api_key(allure_env_tracker):
    with allure_env_tracker("YOUGILE_API_KEY"):
        key = os.getenv("YOUGILE_API_KEY")

    invalid_keys = [None, "", "your-real-x-api-key-here", "test-key", "null"]
    if not key or key in invalid_keys:
        if ALLURE_AVAILABLE:
            allure.attach(
                body=f"Найдено значение: '{key}'",
                name="Критическое значение API ключа",
                attachment_type=allure.attachment_type.TEXT
            )
        pytest.exit(
            "КРИТИЧЕСКАЯ ОШИБКА: Переменная YOUGILE_API_KEY не задана или является заглушкой.",
            returncode=255
        )
    return key


# 6. Фикстура базового URL
@pytest.fixture(scope="session")
def base_url(allure_env_tracker):
    with allure_env_tracker("YOUGILE_API_URL", "https://ru.yougile.com/api-v2"):
        url = os.getenv("YOUGILE_API_URL", "https://ru.yougile.com/api-v2")
    return url


# 7. Фикстура для генерации payload отдела (для сокращения кода тестов)
@pytest.fixture
def department_payload():
    def _make(title=None):
        return {
            "title": title or f"Автотест Отдел {uuid.uuid4()}",
            "parentId": None,
            "users": {}
        }
    return _make