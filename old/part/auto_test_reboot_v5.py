from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime
import time
class WebAutomation:
    def __init__(self, base_url, username, password, loginpwd):
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
        self.loginpwd = loginpwd
    def open_page(self, url):
        self.driver.get(url)
    def login(self):
        try:
            WebDriverWait(self.driver, timeout=TIMEOUT_SEC, poll_frequency=0.7, ).until(
                EC.element_to_be_clickable((By.ID, "submit"))
            )
            username_field = self.driver.find_element(By.ID, "acc")
            password_field = self.driver.find_element(By.ID, "pwd")
            username_field.send_keys(self.username)
            password_field.send_keys(self.password)
            login_button = self.driver.find_element(By.ID, "submit")
            login_button.click()
        except TimeoutException:
            # Handle the timeout exception by refreshing the page
            print("Element was not clickable, refreshing the page.")
            self.driver.refresh()
            # Optionally, you could add logic to retry waiting for the element
            # For example, you could call this function again to retry
            self.login()
    def get_logininfo_pwd(self):
        login_column = self.driver.find_element(By.ID, "Serial_Numb")
        print("get_logininfo_pwd:" + login_column.text)

    def navigate_to_system_tools(self):
        self.open_page(f"{self.base_url}/table.shtml")
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
    def loging_to_page(self):
        # self.click_prompt_test()
        self.login()
        # self.get_logininfo_pwd()
        self.navigate_to_system_tools()
    def click_format_button(self):
        self.find_EVSE_format_but()
        self.find_showConfirmation()
    def find_reboot_but(self):
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
    loginpwd = "8QOJ19Q3"
    TIMEOUT_SEC = 10
    clicks_max = 5
    clicks_now = 1
    show_info = SystemInfo()
    while 1:
        try:
            while clicks_now-1 < clicks_max:
                print("Running %s times:" %clicks_now)
                automation = WebAutomation(base_url, username, password, loginpwd)
                automation.open_page(base_url)
                automation.loging_to_page()
                # automation.find_reboot_but()
                automation.close()
                clicks_now += 1
        finally:
            print("Exception")
            automation.close()
            # continue