from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime
import time
class WebAutomation:
    def __init__(self, base_url, username, password):
        chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument("--incognito")
        # chrome_options.add_argument("--disable-extensions")
        # chrome_options.add_argument("--disable-plugins ")
        # chrome_options.add_argument("--disable-popup-blocking")
        self.driver = webdriver.Chrome(options=chrome_options) #Chrome may not work when typing info
        # self.driver = webdriver.Edge()
        # self.driver = webdriver.Firefox()
        self.base_url = base_url
        self.username = username
        self.password = password
        self.click_count = 0
    def open_page(self, url):
        self.driver.get(url)
    def login(self):
        try:
            WebDriverWait(self.driver, timeout=TIMEOUT_SEC, poll_frequency=0.7, ).until(
                EC.element_to_be_clickable((By.ID, "submit"))
            )
            print("Now window title:", self.driver.title)
            self.original_window = self.driver.current_window_handle
            username_field = self.driver.find_element(By.ID, "acc")
            password_field = self.driver.find_element(By.ID, "pwd")
            username_field.send_keys(self.username)
            password_field.send_keys(self.password)
            login_button = self.driver.find_element(By.ID, "submit")
            login_button.click()
            WebDriverWait(self.driver, 10).until(EC.number_of_windows_to_be(2))
        except TimeoutException:
            print("Element was not clickable, refreshing the page.")
            self.driver.refresh()
            self.login()
    def switch_next_tab(self):
        handles = self.driver.window_handles
        new_window = [handle for handle in handles if handle != self.original_window][0]
        self.driver.switch_to.window(new_window)
        print("Now window title:", self.driver.title)
    def get_logininfo_pwd(self):
        try:
            WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.ID, "but_Login_Account"))
            )
            checkbox = self.driver.find_element(By.XPATH, '//input[@type="checkbox"][@onclick="ShowPwd()"]')
            checkbox.click()
            Login_Password = self.driver.find_element(By.ID, "Login_Password")
            self.loginpwd = Login_Password.get_attribute('value')
        except TimeoutException:
            print("loging_to_page was not clickable, refreshing the page.")
            self.driver.refresh()
            self.get_logininfo_pwd()
    def navigate_to_system_tools(self):
        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "System Tools"))
        )
        system_tool_button = self.driver.find_element(By.LINK_TEXT, "System Tools")
        system_tool_button.click()
    def find_EVSE_format_but(self):
        # Locate and click the format button
        format_button = self.driver.find_element(By.ID, "EVSE_format_but")
        format_button.click()
    def find_showConfirmation(self):
        # ref: https://www.cnblogs.com/Neeo/articles/11465005.html
        wait = WebDriverWait(self.driver, timeout=2)
        alert = wait.until(lambda d : d.switch_to.alert)
        print(alert.text)  
        print("fill into:" + self.loginpwd)
        alert.send_keys(self.loginpwd)
        alert.accept() #equal click OK
    def click_prompt_test(self):
        promptButton = self.driver.find_element(By.ID, "promptButton")
        promptButton.click()
        self.find_showConfirmation()            
    def click_format_button(self):
        self.find_EVSE_format_but()
        self.find_showConfirmation()
    def click_reboot_but(self):
        reboot_button = self.driver.find_element(By.ID, "Reset_but")
        reboot_button.click()
    def close(self):
        self.driver.quit()
class SystemInfo:
    def __init__(self):
        currentDateAndTime = datetime.now()
        print("Start time:", currentDateAndTime)
if __name__ == "__main__":
    base_url = "http://192.168.3.110"
    # base_url = "file:///D:/Foxconn/EVSE/Dev_relate/Code/bot_trv_web/alt.html"
    username = "Foxconn"
    password = "fxnfxn"
    # loginpwd = "8QOJ19Q3"
    TIMEOUT_SEC = 10
    MAX_TEST_TIME = 1000
    now_test_time = 1
    show_info = SystemInfo()
    while 1:
        try:
            while now_test_time-1 < MAX_TEST_TIME:
                print("Running %s times:" %now_test_time)
                automation = WebAutomation(base_url, username, password)
                automation.open_page(base_url)
                automation.login()
                automation.switch_next_tab()
                automation.get_logininfo_pwd()
                automation.navigate_to_system_tools()
                # automation.click_reboot_but()
                automation.click_format_button()
                time.sleep(160)
                automation.close()
                now_test_time += 1
        finally:
            print("Exception")
            automation.close()
            now_test_time -= 1
            continue