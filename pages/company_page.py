from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec

from pages.base_page import BasePage, Locator


class CompanyPage(BasePage):
    """Страница «Моя компания»: отделы и сотрудники."""

    SIDEBAR_COMPANY: Locator = (
        By.XPATH,
        "(//*[normalize-space(.)='Моя компания'])[1]",
    )

    ADD_DEPARTMENT_BUTTON: Locator = (
        By.XPATH,
        "//span[normalize-space(.)='Добавить отдел']",
    )

    DEPARTMENT_NAME_INPUT: Locator = (
        By.XPATH,
        "//*[@placeholder='Введите название отдела']",
    )

    CREATE_DEPARTMENT_BUTTON = (
        By.XPATH,
        '//div[@role="button" and .//div[normalize-space()="Создать отдел"]]'
    )

    @staticmethod
    def department_row(title: str) -> Locator:
        """Отдел с заданным названием."""
        return (
            By.XPATH,
            f"//*[normalize-space(.)='{title}']",
        )

    @staticmethod
    def department_link(title: str) -> Locator:
        """Отдел с заданным названием в списке."""
        return (
            By.XPATH,
            f"//*[normalize-space(.)='{title}']",
        )

    @staticmethod
    def employee_row(email: str) -> Locator:
        """Сотрудник в списке «Сотрудники компании»."""
        return (
            By.XPATH,
            f"(//div[normalize-space() = 'E-mail']",
        )

    @staticmethod
    def dialog_employee_checkbox(email: str) -> Locator:
        """Кликабельный чекбокс сотрудника в окне отдела."""
        row = (
            "//div[contains(@class,'department-users-table__item')]"
            f"[.//span[normalize-space(@title)='{email}']]"
        )
        return (
            By.XPATH,
            f"{row}//div[contains(@class,'department-users-table__item-tick')]"
            f"//div[contains(@class,'cursor-pointer')]",
        )

    @staticmethod
    def dialog_employee_checkbox_state(email: str) -> Locator:
        """Внутренний div чекбокса для проверки состояния."""
        row = (
            "//div[contains(@class,'department-users-table__item')]"
            f"[.//span[normalize-space(@title)='{email}']]"
        )
        return (
            By.XPATH,
            f"{row}//div[contains(@class,'department-users-table__item-tick')]"
            f"//div[contains(@class,'cursor-pointer')]/div[1]",
        )

    @staticmethod
    def profile_department_checkbox(department: str) -> Locator:
        """Чекбокс отдела в профиле сотрудника."""
        label = (
            "//label[contains(@class,'prj-users-ch')]"
            f"[.//span[contains(@class,'prj-invite__item-text') "
            f"and normalize-space(.)='{department}']]"
        )
        return (By.XPATH, f"{label}//input[@type='checkbox']")

    def open_company_section(self) -> None:
        """Перейти в раздел «Моя компания»."""
        self.click(self.SIDEBAR_COMPANY)
        self.find_visible(self.ADD_DEPARTMENT_BUTTON)

    def add_department(self, title: str) -> None:
        """Создать отдел и дождаться его появления в списке."""
        self.click(self.ADD_DEPARTMENT_BUTTON)
        self.type_text(self.DEPARTMENT_NAME_INPUT, title)
        self.click(self.CREATE_DEPARTMENT_BUTTON)

        self.wait.until(
            ec.invisibility_of_element_located(
                self.DEPARTMENT_NAME_INPUT
            )
        )

        # Ждём не только закрытия формы, но и появления отдела.
        self.wait.until(
            ec.presence_of_element_located(
                self.department_row(title)
            )
        )

    def is_department_in_list(self, title: str) -> bool:
        """Проверить наличие отдела в списке."""
        return self.is_visible(self.department_row(title))

    def is_employee_checkbox_checked_in_dialog(
        self,
        email: str,
    ) -> bool:
        """Проверить, отмечен ли сотрудник в окне отдела."""
        element = self.find_visible(
            self.dialog_employee_checkbox_state(email)
        )
        classes = element.get_attribute("class") or ""
        return "bg-action-default" in classes

    def open_department(self, title: str) -> None:
        """Открыть окно редактирования отдела."""
        locator = self.department_link(title)

        self.wait.until(
            ec.presence_of_element_located(locator)
        )

        self.js_click(locator)

        self.find_visible(
            (
                By.XPATH,
                "//*[normalize-space(.)='Редактирование отдела']",
            )
        )

    def add_employee_to_department(
        self,
        department: str,
        email: str,
    ) -> None:
        """Добавить сотрудника в отдел."""
        self.open_department(department)

        self.js_click(
            self.dialog_employee_checkbox(email)
        )

    def open_employee_profile(self, email: str) -> None:
        """Открыть профиль сотрудника."""
        locator = self.employee_row(email)

        self.wait.until(
            ec.presence_of_element_located(locator)
        )

        self.js_click(locator)

        self.find_visible(
            (
                By.XPATH,
                "//*[contains(normalize-space(.), 'Состоит в отделах')]",
            )
        )

    def is_department_checked_in_profile(
        self,
        department: str,
    ) -> bool:
        """Проверить, отмечен ли отдел в профиле."""
        locator = self.profile_department_checkbox(department)

        try:
            self.wait.until(
                lambda driver: driver.find_element(
                    *locator
                ).is_selected()
            )
            return True
        except TimeoutException:
            return False

    # --- НОВЫЕ ЛОКАТОРЫ ДЛЯ ПРИГЛАШЕНИЯ ---
    EMPLOYEES_SECTION: Locator = (
        By.XPATH,
        "//div[contains(@class, 'sidebar')]//span[normalize-space(.)='Добавить сотрудника']"
    )

    INVITE_EMPLOYEE_BUTTON: Locator = (
        By.XPATH,
        "//*[normalize-space(.)='Пригласить сотрудников по почте']"
    )

    INVITE_EMPLOYEE_HELLO:Locator = (
        By.XPATH,
        "// *[contains(text(), 'Приглашение в компанию')]"
    )


    INVITE_EMAIL_INPUT: Locator = (
        By.XPATH,
        "//*[@placeholder='Email адреса']"
    )

    SEND_INVITE_BUTTON: Locator = (
        By.XPATH,
        "//*[normalize-space(.)='Пригласить сотрудников']"
    )

    INVITATION_ROW_TEMPLATE: Locator = (
        By.XPATH,
        f"//tr[.//td[normalize-space()='{{email}}']]"
    )

    INVITATION_STATUS_TEMPLATE: Locator = (
        By.XPATH,
        f"//tr[.//td[normalize-space()='{{email}}']]//td[contains(@class, 'status')]"
    )

    # --- НОВЫЕ МЕТОДЫ ---

    def open_employees_section(self) -> None:
        """Перейти в раздел «Сотрудники» через боковое меню."""
        # Используем js_click, чтобы обойти блокировки и перекрытия
        self.js_click(self.EMPLOYEES_SECTION)

        # Ждем индикатор загрузки раздела.
        # Используем заголовок раздела, так как кнопка приглашения может быть скрыта правами доступа.
        self.find_visible(
            (
                By.XPATH,
                "//*[normalize-space(.)='Сотрудники компании' or normalize-space(.)='Моя компания']"
            )
        )

    def click_invite_employee_button(self) -> None:
        """Нажать на кнопку открытия формы приглашения."""
        self.click(self.INVITE_EMPLOYEE_BUTTON)
        # Ждем появления поля ввода email
        self.find_visible(self.INVITE_EMAIL_INPUT)

    def invite_employee_by_email(self, email: str) -> None:
        """Заполнить email в форме и отправить приглашение."""
        self.type_text(self.INVITE_EMAIL_INPUT, email)
        self.click(self.SEND_INVITE_BUTTON)

        # Ждем закрытия модального окна по исчезновению поля ввода
        try:
            self.wait.until(ec.invisibility_of_element_located(self.INVITE_EMAIL_INPUT))
        except TimeoutException:
            # Если окно не закрылось, возможно, появилась ошибка валидации
            pass

    def is_invitation_in_list(self, email: str) -> bool:
        """Проверяет наличие строки с этим email в таблице приглашений."""
        try:
            self.wait.until(ec.presence_of_element_located(
                self.INVITATION_ROW_TEMPLATE.format(email=email)
            ))
            return True
        except TimeoutException:
            return False

    def get_invitation_status(self, email: str) -> str:
        """Возвращает текст статуса для конкретного приглашения."""
        element = self.find_visible(
            self.INVITATION_STATUS_TEMPLATE.format(email=email)
        )
        return element.text.strip()
