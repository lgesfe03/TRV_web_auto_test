from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime
from tkinter import messagebox

import tkinter as tk
import tkinter.simpledialog
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
ERR_RETRY_OPENPAGE = 3
ERR_RETRY_LOGIN = 3
TIME_GAP_SECONDS_REBOOT = 20
TIME_GAP_SECONDS_RESET_DEFAULT = 20
TIME_GAP_SECONDS_RESET_FORMAT = 160

class TRV_TEST_COMMAND(enum.IntEnum):
    REBOOT = 1
    RESET_DEFAULT = 2
    RESET_FORMAT = 3
class ERROR_ENUM(enum.IntEnum):
    ERR_NONE = 0
    ERR_OPEN_URL = enum.auto()
    ERR_LOGIN_TIMEOUT = enum.auto()
    ERR_LOGIN_OTHER = enum.auto()
    ERR_OPEN_PAGE = enum.auto()
    ERR_RETRY_OUT = enum.auto()

class SystemInfo:
    def __init__(self):
        self.now_test_time = 0
        self.sleep_start_time = 0
        self.sleep_second = 0
        self.command = 0
        self.command_string = ""
        self.starttime = None
        self.endtime = None
        self.max_test_time = 0
        self.err_openpage = 0
        self.err_login = 0
    def max_test_time_get(self):
        return self.max_test_time
    def max_test_time_set(self, number):
        self.max_test_time = number
    def now_test_time_get(self):
        return self.now_test_time
    def now_test_time_add(self):
        self.now_test_time += 1
    def now_test_time_minus(self):
        self.now_test_time -= 1
    def timestamp_start(self):
        self.starttime = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    def timestamp_end_get(self):
        return self.endtime
    def timestamp_end_set(self):
        self.endtime = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    def test_command_set(self, cmd):
        self.timestamp_start()
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
    def err_time_open_page_add(self):
        self.err_openpage += 1
    def err_time_open_page_get(self):
        return self.err_openpage
        
    def err_time_login_add(self):
        self.err_login += 1
    def err_time_login_get(self):
        return self.err_login
    
    def timestamp_before_sleep_set(self):
        self.sleep_start_time = time.time()
    def timestamp_before_sleep_get(self):
        return self.sleep_start_time

    def sleep_time_second_set(self, sec):
        self.sleep_second = sec
    def sleep_time_second_get(self):
        return self.sleep_second
class WebAutomation:
    def __init__(self, base_url, username, password, SystemInfo_instance):
        self.sys = SystemInfo_instance
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
    def open_page(self, url):
        self.driver.get(url)
        # Check if the current URL is the same as the target URL
        current_url = self.driver.current_url
        if current_url != url and current_url != url+"/":
            print(f"Current URL:{current_url} ; Expected:{url} ")
            return ERROR_ENUM.ERR_OPEN_URL
        else:
            return ERROR_ENUM.ERR_NONE
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
            return ERROR_ENUM.ERR_NONE
        except TimeoutException:
            print("Exception: TimeoutException,Element ID:submit was not clickable, refreshing the page.")
            return ERROR_ENUM.ERR_LOGIN_TIMEOUT
        except :
            print("Exception: loing")
            return ERROR_ENUM.ERR_LOGIN_OTHER
    def refresh_page(self):
        self.driver.refresh()
        
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
        match cmd:
            case TRV_TEST_COMMAND.REBOOT:
                self.click_reboot_but()
                self.sys.sleep_time_second_set(TIME_GAP_SECONDS_REBOOT)
            case TRV_TEST_COMMAND.RESET_DEFAULT:
                self.click_default_button()
                self.sys.sleep_time_second_set(TIME_GAP_SECONDS_RESET_DEFAULT)
            case TRV_TEST_COMMAND.RESET_FORMAT:
                self.click_format_button()
                self.sys.sleep_time_second_set(TIME_GAP_SECONDS_RESET_FORMAT)
    def close(self):
        self.driver.quit()

class ScriptAction:
    def __init__(self, SystemInfo_instance):
        self.signal_flag = threading.Event()# Shared flag for signaling
        self.sys = SystemInfo_instance
    def open_page_retry(self):
        if(self.automation.open_page(BASE_URL) != ERROR_ENUM.ERR_NONE):
            self.sys.err_time_open_page_add()
            if(self.sys.err_time_open_page_get() > ERR_RETRY_OPENPAGE):
                return ERROR_ENUM.ERR_RETRY_OUT
            else:
                self.open_page_retry()
    def login_retry(self):
        if(self.automation.login() != ERROR_ENUM.ERR_NONE):
            self.sys.err_time_login_add()
            if(self.sys.err_time_login_get() > ERR_RETRY_LOGIN):
                return ERROR_ENUM.ERR_RETRY_OUT
            else:
                self.automation.refresh_page()
                self.login_retry
    def fail_stop(self):
        self.sys.timestamp_end_set()
        self.automation.close()
    def test_script(self):
        try:
            while 1:
                self.automation = WebAutomation(BASE_URL, USERNAME, PASSWORD, self.sys)
                if(self.open_page_retry()):
                    self.fail_stop()
                    break
                if(self.login_retry()):
                    self.fail_stop()
                    break
                self.automation.switch_next_tab()
                self.automation.get_logininfo_pwd()
                self.automation.run_command(self.sys.test_command_get())
                self.sys.now_test_time_add()
                if  self.sys.max_test_time_get() > 0 and self.sys.now_test_time_get() >= self.sys.max_test_time_get():
                    self.sys.timestamp_end_set()
                    print("Reach Max test times")
                    time.sleep(3) #Format action require wait TRV to complete
                    self.automation.close()
                    break
                self.sys.timestamp_before_sleep_set()
                time.sleep(self.sys.sleep_time_second_get())
                self.automation.close()
        except Exception as err: 
            print(f"ScriptAction Unexpected {err=}, {type(err)=}")
            self.fail_stop()
        finally:
            print("ScriptAction done")
            # continue
    def test_thread(self):
        print("Monitor thread started. Waiting for the signal...")
        while True:
            self.signal_flag.wait()  # Wait for the signal
            self.signal_flag.clear()  # Reset the signal flag
            self.test_script()
    def start(self):
        threading.Thread(target=self.test_thread, daemon=True).start()
        
class GUI_panel:
    def __init__(self, SystemInfo_instance, ScriptAction_instance):
        self.locked = False
        self.sys = SystemInfo_instance
        self.scrt = ScriptAction_instance
        self.root = tk.Tk()
        self.root.title("TRV test script")
        # Create a frame for the buttons
        frame_1 = tk.Frame(self.root)
        frame_2 = tk.Frame(self.root)
        # Create and add buttons to the frame
        self.instruction_label = tk.Label(frame_1, text="Choose below test command for running:")
        self.instruction_label.pack(padx=5, pady=5)
        self.button_reboot = tk.Button(frame_1, text="Reboot", command=self.btn_reboot, width=20)
        self.button_reboot.pack(padx=5, pady=5)
        self.button_default = tk.Button(frame_1, text="Default", command=self.btn_reset_default, width=20)
        self.button_default.pack(padx=5, pady=5)
        self.button_format = tk.Button(frame_1, text="Format", command=self.btn_reset_format, width=20)
        self.button_format.pack(padx=5, pady=5)

        self.button_infinite = tk.Button(frame_1, text="Infinite Loop", command=self.btn_infinite)
        self.button_infinite.pack(side=tk.LEFT, padx=5)
        self.button_finite = tk.Button(frame_1, text="Finite Loop", command=self.btn_finite)
        self.button_finite.pack(side=tk.LEFT,pady=5)
        frame_1.pack()

        self.status_label = tk.Label(frame_2, text="Action taken: None")
        self.status_label.pack(pady=20)
        frame_2.pack()
    def update_instruction_label(self, str):
        self.instruction_label.config(text=str)
    def button_lock(self):
         if not self.locked:
             self.locked = True
             self.update_instruction_label("Running script...")
             self.button_reboot.config(state='disabled')
             self.button_default.config(state='disabled')
             self.button_format.config(state='disabled')
             self.button_infinite.config(state='disabled')
             self.button_finite.config(state='disabled')
    def button_action(self):
        self.scrt.signal_flag.set()
        self.button_lock()
    def btn_reboot(self):
        self.sys.test_command_set(TRV_TEST_COMMAND.REBOOT)
        self.button_action()

    def btn_reset_default(self):
        self.sys.test_command_set(TRV_TEST_COMMAND.RESET_DEFAULT)
        self.button_action()

    def btn_reset_format(self):
        self.sys.test_command_set(TRV_TEST_COMMAND.RESET_FORMAT)
        self.button_action()
    def btn_infinite(self):
        self.sys.max_test_time_set(0)
    def btn_finite(self):
        num_iterations = tkinter.simpledialog.askinteger("Finite Loop", "Enter the number of iterations:")
        if num_iterations > 0:
            self.sys.max_test_time_set(num_iterations)
    def update_task(self):
        target_time = self.sys.max_test_time_get() if self.sys.max_test_time_get() else "infinite"
        self.status_label.config(justify="left", text=f"Action: {self.sys.test_command_string_get()}, \nStartTime: {self.sys.starttime }\nTarget Time: {target_time}, \nRunning Times: {self.sys.now_test_time_get()}")
        if self.sys.timestamp_end_get() != None:
            if not self.scrt.signal_flag.is_set() and self.sys.now_test_time_get() >= self.sys.max_test_time_get() and self.sys.max_test_time_get()>0:
                self.update_instruction_label(f"Test completed at {self.sys.endtime}")
            else:
                self.update_instruction_label(f"Test Failed at {self.sys.endtime}")
        elif self.locked:
            elapsed_time = time.time() - self.sys.timestamp_before_sleep_get()
            remaining_time = max(0, self.sys.sleep_time_second_get() - elapsed_time)
            if remaining_time > 0:
                self.update_instruction_label(f"Running script.. sleep {remaining_time:.0f} seconds for next run")
            else:
                self.update_instruction_label(f"Running script..")
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