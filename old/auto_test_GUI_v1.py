from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime
from tkinter import messagebox

import tkinter as tk
import time
import enum
import os
import threading
# Parameter
BASE_URL = "http://192.168.3.110"
# base_url = "file:///D:/Foxconn/EVSE/Dev_relate/Code/bot_trv_web/alt.html"
USERNAME = "Foxconn"
PASSWORD = "fxnfxn"
# loginpwd = "8QOJ19Q3"
TIMEOUT_SEC = 10
MAX_TEST_TIME = 1000

class TRV_TEST_COMMAND(enum.IntEnum):
    REBOOT = 1
    RESET_DEFAULT = 2
    RESET_FORMAT = 3
    
class WebAutomation:
    def __init__(self, base_url, username, password):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--ignore-certificate-errors')
        # chrome_options.add_argument("--incognito")
        # chrome_options.add_argument("--disable-extensions")
        # chrome_options.add_argument("--disable-plugins ")
        # chrome_options.add_argument("--disable-popup-blocking")
        # Redirect output to a file or suppress it
        self.driver = webdriver.Chrome(options=chrome_options) #Chrome may not work when typing info
        # self.driver = webdriver.Edge()
        # self.driver = webdriver.Firefox()
        self.base_url = base_url
        self.username = username
        self.password = password
        self.click_count = 0
        self.sleep_second = 0
    def open_page(self, url):
        self.driver.get(url)
    def login(self):
        try:
            WebDriverWait(self.driver, timeout=TIMEOUT_SEC, poll_frequency=0.7, ).until(
                EC.element_to_be_clickable((By.ID, "submit"))
            )
            # print("Now window title:", self.driver.title)
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
        # print("Now window title:", self.driver.title)
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
    def find_EVSE_default_but(self):
        format_button = self.driver.find_element(By.ID, "Reset2Default_but")
        format_button.click()
    def find_EVSE_format_but(self):
        format_button = self.driver.find_element(By.ID, "EVSE_format_but")
        format_button.click()
    def alert_reset_default(self):
        wait = WebDriverWait(self.driver, timeout=2)
        alert = wait.until(lambda d : d.switch_to.alert)
        alert.accept() #equal click OK      
    def alert_reset_format(self):
        # ref: https://www.cnblogs.com/Neeo/articles/11465005.html
        wait = WebDriverWait(self.driver, timeout=2)
        alert = wait.until(lambda d : d.switch_to.alert)
        print(alert.text)  
        print("fill into:" + self.loginpwd)
        alert.send_keys(self.loginpwd)
        alert.accept() #equal click OK       
    def click_reboot_but(self):
        reboot_button = self.driver.find_element(By.ID, "Reset_but")
        reboot_button.click()
    def click_default_button(self):
        self.find_EVSE_default_but()
        self.alert_reset_default()
    def click_format_button(self):
        self.find_EVSE_format_but()
        self.alert_reset_format()
    def run_command(self, cmd):
        self.navigate_to_system_tools()
        self.sleep_second = 0
        match cmd:
            case TRV_TEST_COMMAND.REBOOT:
                self.click_reboot_but()
                self.sleep_second = 20
            case TRV_TEST_COMMAND.RESET_DEFAULT:
                self.click_default_button()
                self.sleep_second = 20
            case TRV_TEST_COMMAND.RESET_FORMAT:
                self.click_format_button()
                self.sleep_second = 160
    def close(self):
        self.driver.quit()

class ScriptAction:
    def __init__(self, SystemInfo_instance):
        self.signal_flag = threading.Event()# Shared flag for signaling
        self.sys = SystemInfo_instance
    def test_script(self):
        try:
            while self.sys.now_test_time_get()-1 < MAX_TEST_TIME:
                automation = WebAutomation(BASE_URL, USERNAME, PASSWORD)
                automation.open_page(BASE_URL)
                automation.login()
                automation.switch_next_tab()
                automation.get_logininfo_pwd()
                automation.run_command(self.sys.test_command_get())
                self.sys.now_test_time_add()
                time.sleep(automation.sleep_second)
                automation.close()
        finally:
            print("Exception ScriptAction")
            self.sys.now_test_time_minus()
            # continue
    def test_thread(self):
        print("Monitor thread started. Waiting for the signal...")
        while True:
            self.signal_flag.wait()  # Wait for the signal
            self.signal_flag.clear()  # Reset the signal flag
            self.test_script()
    def start(self):
        threading.Thread(target=self.test_thread, daemon=True).start()

class SystemInfo:
    def __init__(self):
        self.now_test_time = 1
        self.command = 0
        self.command_string = ""
        self.starttime = None
    def now_test_time_get(self):
        return self.now_test_time
    def now_test_time_add(self):
        self.now_test_time += 1
    def now_test_time_minus(self):
        self.now_test_time -= 1
    def test_command_set(self, cmd):
        self.starttime = datetime.now().strftime('%Y/%m/%d_%H:%M:%S')
        print("Start time:", self.starttime)
        match cmd:
            case TRV_TEST_COMMAND.REBOOT:
                self.command = TRV_TEST_COMMAND.REBOOT
                self.command_string = "Reboot"
            case TRV_TEST_COMMAND.RESET_DEFAULT:
                self.command = TRV_TEST_COMMAND.RESET_DEFAULT
                self.command_string = "Reset_DEFAULT"
            case TRV_TEST_COMMAND.RESET_FORMAT:
                self.command = TRV_TEST_COMMAND.RESET_FORMAT
                self.command_string = "Reset_FORMAT"
    def test_command_get(self):
        return self.command
    def test_command_string_get(self):
        return self.command_string

class GUI_panel:
    def __init__(self, SystemInfo_instance, ScriptAction_instance):
        self.locked = False
        self.sys = SystemInfo_instance
        self.scrt = ScriptAction_instance
        self.root = tk.Tk()
        self.root.title("TRV test script")
        # Create a frame for the buttons
        frame = tk.Frame(self.root)
        frame.pack(padx=10, pady=10)
        # Create and add buttons to the frame
        instruction_label = tk.Label(frame, text="Choose below test command for running:")
        instruction_label.pack(pady=5)
        self.button_reboot = tk.Button(frame, text="Reboot", command=self.reboot, width=20)
        self.button_reboot.pack(pady=5)
        self.button_default = tk.Button(frame, text="Default", command=self.reset_default, width=20)
        self.button_default.pack(pady=5)
        self.button_format = tk.Button(frame, text="Format", command=self.reset_format, width=20)
        self.button_format.pack(pady=5)
        self.status_label = tk.Label(frame, text="Action taken: None")
        self.status_label.pack(pady=10)
    def button_lock(self):
         if not self.locked:
             self.locked = True
             self.button_reboot.config(state='disabled')
             self.button_default.config(state='disabled')
             self.button_format.config(state='disabled')

    def button_action(self):
        self.scrt.signal_flag.set()
        self.button_lock()

    def reboot(self):
        self.sys.test_command_set(TRV_TEST_COMMAND.REBOOT)
        self.button_action()

    def reset_default(self):
        self.sys.test_command_set(TRV_TEST_COMMAND.RESET_DEFAULT)
        self.button_action()

    def reset_format(self):
        self.sys.test_command_set(TRV_TEST_COMMAND.RESET_FORMAT)
        self.button_action()

    def update_task(self):
        self.status_label.config(justify="left", text=f"Action: {self.sys.test_command_string_get()}, \nStartTime: {self.sys.starttime }\nRunning Times: {self.sys.now_test_time_get()-1}")
        self.root.after(1000, self.update_task)

    def run_gui(self):
        # Start the periodic task
        self.update_task()
        # This method will run in a separate thread
        self.root.mainloop()
    
if __name__ == "__main__":
    sys = SystemInfo()

    test = ScriptAction(sys)
    test.start()
    
    gui = GUI_panel(sys, test)
    gui.run_gui()