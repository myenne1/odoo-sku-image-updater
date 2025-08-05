from playwright.sync_api import sync_playwright, Page
from typing import List, Set
from configurations.config import settings

class Navigator:
    def __init__(self):
        self.username = settings.ALTHEA_USERNAME
        self.password = settings.ALTHEA_PASSWORD
        self.base_url = settings.ALTHEA_LOGIN_URL
        self.browser = None
        self.page: Page = None
        self.context = None
        self.playwright = None

    def launch(self, headless=True):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        print("[*] Browser launched.")

    def login(self):
        print("[*] Logging in...")
        self.page.goto(f"{self.base_url}")
        self.page.fill('input[name="txtUserName"]', self.username)
        
        self.page.fill('input[name="txtPassword"]', self.password)
        self.page.click('input[name="BtnLogin"]')
        
        self.page.wait_for_url("**/Application.aspx#", timeout=15000)        
        print("[+] Login successful.")

        
    def navigate_to_database(self):
        print("[*] Navigating to Database...")
        
        self.page.click('button[data-target="#Sub_btnProducts"]')
        self.page.click('button[data-target="#Sub_btnManageItem"]')
        
        self.page.wait_for_load_state("networkidle")
        print("[+] Opened Items ")
        
    def click_next(self, page_number):
        try:
            selector = f"a[href='javascript:void(0);'][onclick*=\"GotoPage('{page_number}')\"]"
            next_button = self.page.locator(selector)
            
            if next_button.is_visible():
                next_button.click()
                self.page.wait_for_load_state("networkidle")
                print(f"[+] Moved to page {page_number}")
                return True
            else:
                print(f"[!] Button for page {page_number} not visible")
                return False

        except Exception as e:
            print(f"[!] Failed to go to page {page_number}: {e}")
            return False

        
    def close(self):
        self.browser.close()
        self.playwright.stop()
        print("[*] Browser closed.")
        
    def run(self, headless=True):
        self.launch(headless=headless)
        self.login()
        self.navigate_to_database()
        