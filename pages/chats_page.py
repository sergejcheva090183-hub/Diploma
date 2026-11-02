from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from pages.base_page import BasePage, Locator

CHECKBOX = ".//div[@role='checkbox']"
CLICK_BUTTON_SCRIPT = (
    "const target = arguments[0].closest('button, [role=\"button\"]')"
    " || arguments[0]; target.click();"
)


class ChatsPage(BasePage):
    """Страница «Мессенджер» (Чаты) в YouGile."""

    SIDEBAR_MESSENGER: Locator = (
        By.XPATH,
        "//*[normalize-space(text())='Чаты']"
    )
    CREATE_CHAT_ICON: Locator = (
        By.XPATH,
        "//*[local-name()='svg' and @data-icon='IconUserPlus']",
    )
    MENU_CREATE_GROUP_CHAT = (
        By.XPATH,
        '//*[@data-testid="create-chat-menu-trigger"]'
    )

    CHAT_NAME_INPUT = (
        By.CSS_SELECTOR,
        'input[placeholder="Введите название группового чата"]'
    )
    CREATE_CHAT_BUTTON = (
        By.XPATH,
        '//div[@role="button" and contains(.//span, "Создать чат")]'
    )

    MESSAGE_FIELD: Locator = (
        By.CSS_SELECTOR,
        "div.ck-editor__editable[contenteditable='true']",
    )

    @staticmethod
    def _row_xpath(email: str) -> str:
        return (
            "//div[@data-testid='employee-sticker-field-list']"
            f"[.//span[normalize-space(text())='{email}']]"
        )

    def _first_visible(self, locator: Locator, timeout: int | None = None) -> WebElement:
        def pick(driver: WebDriver) -> WebElement | bool:
            for element in driver.find_elements(*locator):
                try:
                    if element.is_displayed():
                        return element
                except StaleElementReferenceException:
                    continue
            return False
        wait = WebDriverWait(self.driver, timeout) if timeout else self.wait
        return wait.until(pick)

    def open_messenger(self) -> None:
        self.click(self.SIDEBAR_MESSENGER)
        self.find_visible((By.XPATH, "//*[contains(@placeholder, 'Поиск')]"))

    def _click_menu_real(self) -> None:
        item = self._first_visible(self.MENU_CREATE_GROUP_CHAT)
        ActionChains(self.driver).move_to_element(item).click().perform()

    def _click_menu_js(self) -> None:
        self.js_click(self.MENU_CREATE_GROUP_CHAT)

    def open_create_group_chat_dialog(self) -> None:
        icon = self.wait.until(ec.presence_of_element_located(self.CREATE_CHAT_ICON))
        try:
            ActionChains(self.driver).move_to_element(icon).click().perform()
        except WebDriverException:
            parent = icon.find_element(By.XPATH, "..")
            self.driver.execute_script("arguments[0].click();", parent)
        for click in (self._click_menu_real, self._click_menu_js):
            try:
                click()
                self._first_visible(self.CHAT_NAME_INPUT, timeout=4)
                return
            except WebDriverException:
                continue
        raise AssertionError("Окно создания группового чата не открылось")

    def fill_chat_name(self, name: str) -> None:
        field = self._first_visible(self.CHAT_NAME_INPUT)
        field.click()
        field.send_keys(Keys.CONTROL, "a")
        field.send_keys(Keys.BACKSPACE)
        field.send_keys(name)

    def _visible_rows(self, email: str) -> list[WebElement]:
        rows = self.driver.find_elements(By.XPATH, self._row_xpath(email))
        visible: list[WebElement] = []
        for row in rows:
            try:
                if row.is_displayed():
                    visible.append(row)
            except StaleElementReferenceException:
                continue
        return visible

    def _checkbox(self, email: str) -> WebElement:
        return self._visible_rows(email)[0].find_element(By.XPATH, CHECKBOX)

    def _is_checked(self, email: str) -> bool:
        try:
            return self._checkbox(email).get_attribute("aria-checked") == "true"
        except (IndexError, WebDriverException):
            return False

    def _wait_checked(self, email: str, timeout: int = 3) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(lambda _: self._is_checked(email))
            return True
        except TimeoutException:
            return False

    def _click_real(self, email: str) -> None:
        box = self._checkbox(email)
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", box)
        ActionChains(self.driver).move_to_element(box).click().perform()

    def _click_js(self, email: str) -> None:
        self.driver.execute_script("arguments[0].click();", self._checkbox(email))

    def _click_row(self, email: str) -> None:
        row = self._visible_rows(email)[0]
        name = row.find_element(By.XPATH, f".//span[normalize-space(text())='{email}']")
        ActionChains(self.driver).move_to_element(name).click().perform()

    def select_employee(self, email: str) -> None:
        self.wait.until(lambda _: self._visible_rows(email))
        for strategy in (self._click_real, self._click_js, self._click_row):
            if self._is_checked(email):
                return
            try:
                strategy(email)
            except WebDriverException:
                continue
            if self._wait_checked(email):
                return
        raise AssertionError(f"Не удалось отметить сотрудника {email}")


    def click_create(self) -> None:
        """
        Находит кнопку 'Создать чат' и ждёт её готовности к обычному клику.
        """
        wait = WebDriverWait(self.driver, 15, poll_frequency=1)

        # Ждём, пока кнопка станет доступна для обычного клика
        button = wait.until(
            EC.element_to_be_clickable(self.CREATE_CHAT_BUTTON),
            message="Кнопка 'Создать чат' недоступна для клика за 15 сек."
        )

        # Обычный клик Selenium
        button.click()

    @staticmethod
    def chat_link(chat_name: str) -> Locator:
        return (
            By.XPATH,
            f"//*[contains(@class, 'chat-list') or contains(@class, 'chats-list')]"
            f"//*[normalize-space(text())='{chat_name}']",
        )

    def open_chat(self, chat_name: str) -> None:
        locator = self.chat_link(chat_name)
        self.wait.until(ec.presence_of_element_located(locator))
        self.js_click(locator)
        self.find_visible(self.MESSAGE_FIELD)

    def send_message_with_mention(self, user_email: str) -> None:
        """Ввести сообщение с упоминанием и отправить через Enter."""
        field = self.find_visible(self.MESSAGE_FIELD)
        field.click()
        field.send_keys(Keys.CONTROL, "a")
        field.send_keys(Keys.BACKSPACE)
        field.send_keys("Привет, @")
        prefix = user_email.split("@")[0]
        field.send_keys(prefix[:3])
        self.wait.until(ec.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{user_email}')]")))
        field.send_keys(Keys.ENTER)
        self.wait.until(ec.presence_of_element_located((By.XPATH, f"//*[contains(text(), 'Привет,') and contains(text(), '{user_email}')]")))

    def is_message_sent_with_mention(self, user_email: str) -> bool:
        locator = (By.XPATH, f"//*[contains(text(), 'Привет,') and contains(text(), '{user_email}')]")
        try:
            self.wait.until(ec.presence_of_element_located(locator))
            return True
        except TimeoutException:
            return False