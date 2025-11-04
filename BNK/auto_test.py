from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException
from datetime import datetime
from tkinter import messagebox
from tkinter import filedialog
from pathlib import Path

import tkinter as tk
import tkinter.simpledialog
import time
import enum
import os
import threading
# Parameter
BASE_URL = "https://192.168.5.1/login"
USERNAME = "Foxconn"
PASSWORD = "AM0ANMMB"
IMAGE_A_MPU_VERSION = "02.11.03"
IMAGE_A_MCU_VERSION = "00.00.01"
IMAGE_B_MPU_VERSION = "02.11.01"
IMAGE_B_MCU_VERSION = "00.00.01"
FIRMWARE_IMAGES = {
    IMAGE_A_MPU_VERSION: r"D:\Foxconn\EVSE\Binoki\Image_OTA\20251017_BNK_DVT_MPU_v2.11.3\imx8mpevk-fox.zip",
    IMAGE_B_MPU_VERSION: r"D:\Foxconn\EVSE\Binoki\Image_OTA\20250930_BNK_DVT_MPU_V2.11.1\imx8mpevk-fox.zip",
}
TIMEOUT_SEC = 10
ERR_RETRY_OPENPAGE = 5
ERR_RETRY_LOGIN = 3
TIME_GAP_SECONDS_REBOOT = 45
TIME_GAP_SECONDS_RESET_DEFAULT = 20
TIME_GAP_SECONDS_RESET_FORMAT = 160

class BNK_TEST_COMMAND(enum.IntEnum):
    REBOOT = 1
    RESET_DEFAULT = 2
    RESET_FORMAT = 3
    FW_UPDATE = 4
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
            case BNK_TEST_COMMAND.REBOOT:
                self.command = BNK_TEST_COMMAND.REBOOT
                self.command_string = "Reboot"
            case BNK_TEST_COMMAND.RESET_DEFAULT:
                self.command = BNK_TEST_COMMAND.RESET_DEFAULT
                self.command_string = "Reset_DEFAULT"
            case BNK_TEST_COMMAND.RESET_FORMAT:
                self.command = BNK_TEST_COMMAND.RESET_FORMAT
                self.command_string = "Reset_FORMAT"
            case BNK_TEST_COMMAND.FW_UPDATE:
                self.command = BNK_TEST_COMMAND.FW_UPDATE
                self.command_string = "FW_UPDATE"
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
    def check_info_set(self, mpu_version, mcu_version):
        self.new_mpu_version = mpu_version
        self.new_mcu_version = mcu_version
    def check_info_get(self):
        return self.new_mpu_version, self.new_mcu_version
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
        self.now_mpu_version = ""
        self.now_mcu_version = ""
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
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
            )
            # print("Now window title:", self.driver.title)
            self.original_window = self.driver.current_window_handle
            username_field = self.driver.find_element(By.ID, "loginUsername")
            password_field = self.driver.find_element(By.ID, "loginPassword")
            username_field.send_keys(self.username)
            password_field.send_keys(self.password)
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
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
    def get_MPU_MCU_version(self):
        locator = (By.XPATH, "//h6[normalize-space()='MPU']/following-sibling::p")
        version_el = self.driver.find_element(*locator)
        self.now_mpu_version = version_el.text.strip()
        print("MPU Version:", self.now_mpu_version)

        locator = (By.XPATH, "//h6[normalize-space()='MCU']/following-sibling::p")
        version_el = self.driver.find_element(*locator)
        self.now_mcu_version = version_el.text.strip()
        print("MCU Version:", self.now_mcu_version)
    def navigate_to_system_tools(self):
        wait = WebDriverWait(self.driver, 2)
        system_locator = (By.ID, "navLinkSystem")
        try:
            link = wait.until(EC.element_to_be_clickable(system_locator))
        except TimeoutException:
            toggler = self.driver.find_element(By.CSS_SELECTOR, "button.navbar-toggler")
            if toggler.is_displayed():
                toggler.click()
            link = wait.until(EC.element_to_be_clickable(system_locator))

        link.click()
    def find_EVSE_default_but(self):
        format_button = self.driver.find_element(By.ID, "resetDefaultChkBtn")
        format_button.click()
    def find_EVSE_format_but(self):
        format_button = self.driver.find_element(By.ID, "evseFormatChkBtn")
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
        locator = (By.ID, "powerRestartChkBtn")
        wait = WebDriverWait(self.driver, 10)

        button = wait.until(EC.presence_of_element_located(locator))
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        wait.until(EC.element_to_be_clickable(locator))

        try:
            button.click()
        except ElementClickInterceptedException:
            # give any overlay a moment to slide away—adjust selectors to match your app
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".modal-backdrop.show")))
            try:
                ActionChains(self.driver).move_to_element(button).click().perform()
            except ElementClickInterceptedException:
                self.driver.execute_script("arguments[0].click();", button)
    def confirm_reboot(self):
        modal = (By.ID, "powerRestartModal")
        yes_btn = (By.XPATH, "//div[@id='powerRestartModal']//button[normalize-space()='Yes']")

        WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located(modal))
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(yes_btn)).click()
    def click_default_button(self):
        self.find_EVSE_default_but()
        self.alert_reset_default()
    def click_format_button(self):
        self.find_EVSE_format_but()
        self.alert_reset_format()
    def check_last_fwupdate(self):
        if self.sys.now_test_time_get() == 0:
            print("Skip version check due to first test, Now MPU version:", self.now_mpu_version, "MCU Version:", self.now_mcu_version)
            return
        else:
            target_mpu, target_mcu = self.sys.check_info_get()
            errors = []
            if self.now_mpu_version != target_mpu:
                errors.append(f"MPU version mismatch!\nExpected: {target_mpu}\nCurrent: {self.now_mpu_version}")
            if self.now_mcu_version != target_mcu:
                errors.append(f"MCU version mismatch!\nExpected: {target_mcu}\nCurrent: {self.now_mcu_version}")

            if errors:
                messagebox.showerror("Error", "FW update version mismatch!\n" + "\n".join(errors))
                raise Exception("Check: FW update failed or unknown version!")
            else:
                print("Check: FW Update OK, MPU version:", self.now_mpu_version, "MCU version:", self.now_mcu_version)
    def click_but_fwupdate(self):
        next_version = IMAGE_B_MPU_VERSION if self.now_mpu_version == IMAGE_A_MPU_VERSION else IMAGE_A_MPU_VERSION
        self.sys.check_info_set(next_version, IMAGE_A_MCU_VERSION if next_version == IMAGE_A_MPU_VERSION else IMAGE_B_MCU_VERSION)
        print("FW update : try ", self.now_mpu_version, "->", next_version)
        firmware_path = Path(FIRMWARE_IMAGES[next_version]).expanduser().resolve()
        if not firmware_path.is_file():
            raise FileNotFoundError(f"Firmware ZIP not found: {firmware_path}")

        wait = WebDriverWait(self.driver, 10)
        file_input = wait.until(EC.presence_of_element_located((By.ID, "firmwareFileInput")))
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", file_input)
        file_input.send_keys(str(firmware_path))
        time.sleep(3)
        update_btn_locator = (By.ID, "firmwareUpdateBtn")
        wait.until(lambda d: d.find_element(*update_btn_locator).is_enabled())
        update_btn = wait.until(EC.element_to_be_clickable(update_btn_locator))
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", update_btn)
        update_btn.click()
    
    def wait_fwupdate_progress_complete(self, timeout: int = 120):
        progress_locator = (By.ID, "firmwareProgressBar")
        wait = WebDriverWait(self.driver, timeout)

        wait.until(EC.presence_of_element_located(progress_locator))

        def progress_reached(driver):
            try:
                element = driver.find_element(*progress_locator)
            except StaleElementReferenceException:
                return False

            value_now = element.get_attribute("aria-valuenow")
            if value_now and value_now.isdigit():
                return int(value_now) >= 100

            text_content = element.text.strip()
            if text_content.endswith("%"):
                try:
                    return int(text_content.rstrip("%")) >= 100
                except ValueError:
                    pass

            style_attr = element.get_attribute("style") or ""
            if "width" in style_attr:
                try:
                    width_value = float(style_attr.split("width:")[1].split("%")[0].strip())
                    return width_value >= 100
                except (IndexError, ValueError):
                    return False

            return False

        wait.until(progress_reached)

    def wait_connection_interrupted(self, timeout: int = 240):
        locators = [
            (By.XPATH, "//span[normalize-space()='Your connection was interrupted']"),
            (By.XPATH, "//span[contains(normalize-space(), 'This site can') and contains(normalize-space(), 'be reached')]"),
        ]
        wait = WebDriverWait(self.driver, timeout)

        def message_visible(driver):
            for locator in locators:
                try:
                    element = driver.find_element(*locator)
                    if element.is_displayed():
                        return element
                except (NoSuchElementException, StaleElementReferenceException):
                    continue
            return False

        try:
            element = wait.until(message_visible)
            return element.text.strip() if element else ""
        except TimeoutException:
            return ""
    
    def run_command(self, cmd):
        self.navigate_to_system_tools()
        match cmd:
            case BNK_TEST_COMMAND.FW_UPDATE:
                self.check_last_fwupdate()
                self.click_but_fwupdate()
                self.wait_fwupdate_progress_complete()
                self.wait_connection_interrupted()
                self.sys.sleep_time_second_set(TIME_GAP_SECONDS_REBOOT)
            case BNK_TEST_COMMAND.REBOOT:
                self.click_reboot_but()
                print("Reboot action done, wait for ", TIME_GAP_SECONDS_REBOOT, " seconds")
                self.confirm_reboot()
                print("Reboot confirmed")
                self.sys.sleep_time_second_set(TIME_GAP_SECONDS_REBOOT)
            case BNK_TEST_COMMAND.RESET_DEFAULT:
                self.click_default_button()
                self.sys.sleep_time_second_set(TIME_GAP_SECONDS_RESET_DEFAULT)
            case BNK_TEST_COMMAND.RESET_FORMAT:
                self.click_format_button()
                self.sys.sleep_time_second_set(TIME_GAP_SECONDS_RESET_FORMAT)
    def close(self):
        self.driver.quit()

class ScriptAction:
    def __init__(self, SystemInfo_instance):
        self.signal_flag = threading.Event()# Shared flag for signaling
        self.sys = SystemInfo_instance
        self.skip_sleep_event = threading.Event()
        self.sleep_in_progress = threading.Event()
    def open_page_retry(self):
        while True:
            try:
                result = self.automation.open_page(BASE_URL)
            except WebDriverException as exc:
                print(f"WebDriverException while opening page: {exc}")
                result = ERROR_ENUM.ERR_OPEN_PAGE

            if result == ERROR_ENUM.ERR_NONE:
                return ERROR_ENUM.ERR_NONE

            self.sys.err_time_open_page_add()
            print(f"Open page failed, retry count: {self.sys.err_time_open_page_get()}")
            if self.sys.err_time_open_page_get() > ERR_RETRY_OPENPAGE:
                return ERROR_ENUM.ERR_RETRY_OUT

            try:
                self.automation.close()
            except Exception:
                pass

            time.sleep(1)
            self.automation = WebAutomation(BASE_URL, USERNAME, PASSWORD, self.sys)
    def login_retry(self):
        if self.automation.login() != ERROR_ENUM.ERR_NONE:
            self.sys.err_time_login_add()
            if self.sys.err_time_login_get() > ERR_RETRY_LOGIN:
                return ERROR_ENUM.ERR_RETRY_OUT
            else:
                self.automation.refresh_page()
                return self.login_retry()
        return ERROR_ENUM.ERR_NONE

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
                self.automation.get_MPU_MCU_version()
                self.automation.run_command(self.sys.test_command_get())
                self.sys.now_test_time_add()
                if  self.sys.max_test_time_get() > 0 and self.sys.now_test_time_get() >= self.sys.max_test_time_get():
                    self.sys.timestamp_end_set()
                    print("Reach Max test times")
                    time.sleep(3) #Format action require wait BNK to complete
                    self.automation.close()
                    break
                self.sys.timestamp_before_sleep_set()
                sleep_seconds = self.sys.sleep_time_second_get()
                if sleep_seconds > 0:
                    self.skip_sleep_event.clear()
                    self.sleep_in_progress.set()
                    interrupted = self.skip_sleep_event.wait(timeout=sleep_seconds)
                    self.sleep_in_progress.clear()
                    self.skip_sleep_event.clear()
                    if interrupted:
                        print("Sleep skipped by user request")
                        self.sys.sleep_time_second_set(0)
                self.skip_sleep_event.clear()
                self.automation.close()
        except Exception as err: 
            print(f"ScriptAction Unexpected {err=}, {type(err)=}")
            self.fail_stop()
        finally:
            print("ScriptAction done")
            # continue
    def skip_sleep(self):
        if self.sleep_in_progress.is_set():
            self.sys.sleep_time_second_set(0)
            self.skip_sleep_event.set()
            return True
        return False
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
        self.root.title("BNK test script")
        # Create a frame for the buttons
        frame_1 = tk.Frame(self.root)
        frame_2 = tk.Frame(self.root)
        # Create and add buttons to the frame
        self.instruction_label = tk.Label(frame_1, text="Choose below test command for running:")
        self.instruction_label.pack(padx=5, pady=5)
        
        self.button_fw_update = tk.Button(frame_1, text="FW update", command=self.btn_fwupdate, width=20)
        self.button_fw_update.pack(padx=5, pady=5)

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
        self.button_skipsleep = tk.Button(frame_1, text="Skip Sleep", command=self.btn_skipsleep)
        self.button_skipsleep.pack(side=tk.LEFT,pady=5)
        frame_1.pack()

        self.status_label = tk.Label(frame_2, text="Action taken: None")
        self.status_label.pack(pady=20)
        frame_2.pack()
        self.function_pre_stop()
    def function_pre_stop(self):
        self.button_default.config(state='disabled')
        self.button_format.config(state='disabled')
    def update_instruction_label(self, str):
        self.instruction_label.config(text=str)
    def button_lock(self):
         if not self.locked:
             self.locked = True
             self.update_instruction_label("Running script...")
             self.button_reboot.config(state='disabled')
             self.button_default.config(state='disabled')
             self.button_format.config(state='disabled')
             self.button_fw_update.config(state='disabled')
             self.button_infinite.config(state='disabled')
             self.button_finite.config(state='disabled')
    def button_action(self):
        self.scrt.signal_flag.set()
        self.button_lock()
    def prompt_fwupdate_settings(self):
        global IMAGE_A_MPU_VERSION, IMAGE_A_MCU_VERSION, IMAGE_B_MPU_VERSION, IMAGE_B_MCU_VERSION, FIRMWARE_IMAGES

        def ask_version(prompt, initial):
            value = tkinter.simpledialog.askstring("Firmware Version", prompt, initialvalue=initial)
            if value is None:
                return None
            value = value.strip()
            return value if value else None

        def ask_zip_path(title, current_path):
            initial_dir = ""
            if current_path:
                try:
                    initial_dir = str(Path(current_path).parent)
                except Exception:
                    initial_dir = ""
            file_path = filedialog.askopenfilename(
                title=title,
                filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")],
                initialdir=initial_dir if initial_dir else None
            )
            return file_path if file_path else None

        current_a_path = FIRMWARE_IMAGES.get(IMAGE_A_MPU_VERSION, "")
        current_b_path = FIRMWARE_IMAGES.get(IMAGE_B_MPU_VERSION, "")

        new_a_mpu = ask_version("Enter IMAGE_A_MPU_VERSION", IMAGE_A_MPU_VERSION)
        if not new_a_mpu:
            return False
        new_a_mcu = ask_version("Enter IMAGE_A_MCU_VERSION", IMAGE_A_MCU_VERSION)
        if not new_a_mcu:
            return False
        a_zip = ask_zip_path("Select firmware zip for IMAGE_A", current_a_path)
        if not a_zip:
            messagebox.showinfo("FW update", "Firmware selection cancelled.")
            return False

        new_b_mpu = ask_version("Enter IMAGE_B_MPU_VERSION", IMAGE_B_MPU_VERSION)
        if not new_b_mpu:
            return False
        new_b_mcu = ask_version("Enter IMAGE_B_MCU_VERSION", IMAGE_B_MCU_VERSION)
        if not new_b_mcu:
            return False
        b_zip = ask_zip_path("Select firmware zip for IMAGE_B", current_b_path)
        if not b_zip:
            messagebox.showinfo("FW update", "Firmware selection cancelled.")
            return False

        IMAGE_A_MPU_VERSION = new_a_mpu
        IMAGE_A_MCU_VERSION = new_a_mcu
        IMAGE_B_MPU_VERSION = new_b_mpu
        IMAGE_B_MCU_VERSION = new_b_mcu
        FIRMWARE_IMAGES = {
            IMAGE_A_MPU_VERSION: a_zip,
            IMAGE_B_MPU_VERSION: b_zip,
        }
        self.update_instruction_label("Firmware configuration updated.")
        return True
    def btn_fwupdate(self):
        if not self.prompt_fwupdate_settings():
            return
        self.sys.test_command_set(BNK_TEST_COMMAND.FW_UPDATE)
        self.button_action()
    def btn_reboot(self):
        self.sys.test_command_set(BNK_TEST_COMMAND.REBOOT)
        self.button_action()

    def btn_reset_default(self):
        self.sys.test_command_set(BNK_TEST_COMMAND.RESET_DEFAULT)
        self.button_action()

    def btn_reset_format(self):
        self.sys.test_command_set(BNK_TEST_COMMAND.RESET_FORMAT)
        self.button_action()
    def btn_infinite(self):
        self.sys.max_test_time_set(0)
    def btn_finite(self):
        num_iterations = tkinter.simpledialog.askinteger("Finite Loop", "Enter the number of iterations:")
        if num_iterations > 0:
            self.sys.max_test_time_set(num_iterations)
    def btn_skipsleep(self):
        if self.scrt.skip_sleep():
            self.update_instruction_label("Sleep skipped. Resuming tests...")
        else:
            messagebox.showinfo("Skip Sleep", "No sleep in progress to skip.")
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
