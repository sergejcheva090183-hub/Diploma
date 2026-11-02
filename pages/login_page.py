from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec

from pages.base_page import BasePage, Locator


class LoginPage(BasePage):
    """Страница входа в YouGile."""

    EMAIL_INPUT: Locator = (
        By.CSS_SELECTOR,
        "input[type='email'], input[name='email'], input[name='login']",
    )
    PASSWORD_INPUT: Locator = (By.CSS_SELECTOR, "input[type='password']")

    def login(self, email: str, password: str) -> None:
        """Ввести почту и пароль и отправить форму клавишей Enter."""
        self.type_text(self.EMAIL_INPUT, email)
        self.type_text(self.PASSWORD_INPUT, password)
        self.find_visible(self.PASSWORD_INPUT).send_keys(Keys.ENTER)

    def is_logged_in(self) -> bool:
        """Вход выполнен, если форма с паролем исчезла."""
        try:
            self.wait.until(ec.invisibility_of_element_located(self.PASSWORD_INPUT))
            return True
        except TimeoutException:
            return False