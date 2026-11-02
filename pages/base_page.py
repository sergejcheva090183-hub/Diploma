from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys

Locator = tuple[str, str]

class BasePage:
    """Общие действия для всех страниц. Только явные ожидания"""

    def __init__(self, driver: WebDriver, timeout: int = 20) -> None:
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    def open(self, url: str) -> None:
        self.driver.get(url)

    def js_click(self, locator: Locator) -> None:
        """Клик через JavaScript с предварительным скроллом к элементу."""
        element = self.find_visible(locator)
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        self.driver.execute_script("arguments[0].click();", element)

    def find_visible(self, locator: Locator) -> WebElement:
        return self.wait.until(ec.visibility_of_element_located(locator))

    def click(self, locator: Locator) -> None:
        self.wait.until(ec.element_to_be_clickable(locator)).click()

    def js_click(self, locator: Locator) -> None:
        """Клик через JavaScript для элементов, скрытых стилями (чекбоксы)."""
        element = self.wait.until(ec.presence_of_element_located(locator))
        self.driver.execute_script("arguments[0].click();", element)


    def type_text(self, locator: Locator, text: str) -> None:
        """Ввести текст. Очищает поле через Ctrl+A, Backspace (надёжнее для React)."""
        element = self.find_visible(locator)
        element.click()
        element.send_keys(Keys.CONTROL, "a")
        element.send_keys(Keys.BACKSPACE)
        element.send_keys(text)

    def is_visible(self, locator: Locator) -> bool:
        try:
            self.find_visible(locator)
            return True
        except TimeoutException:
            return False