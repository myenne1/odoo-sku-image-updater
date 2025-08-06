import os
import time
import base64
import hashlib
from playwright.sync_api import Browser
from configurations.config import settings

PAGE_LIMIT = settings.PAGE_LIMIT

class Scraper:
    def __init__(self, page, output_dir: str = "downloaded-images", blank_images: list = []):
        self.output_dir = os.path.abspath(output_dir)
        self.browser: Browser = None
        self.page = page
        self.image_data = []
        self.blank_images = []
        self.seen_hashes = set()
        self.image_hash_map = {} 

        os.makedirs(self.output_dir, exist_ok=True)
        print(f"[+] Images will be saved to: {self.output_dir}")

    def scrape_database(self):
        current_page = 1
        self.wait_for_user()

        while True:
            print(f"\n[*] Scraping page {current_page}...")
            self.page.wait_for_selector('table[style="width:max-content;min-width:100%"]', timeout=15000)
            rows = self.page.locator('table tr').all()
            print(f"# of rows: {len(rows)}")

            if len(rows) <= 1:
                print("[!] No rows found on this page, stopping.")
                break

            for row in rows[1:]:
                cells = row.locator("td").all()
                if len(cells) < 4:
                    continue

                try:
                    sku_element = cells[2].locator("span.clickable-cell-value")
                    sku_num = sku_element.inner_text().strip()
                    item_name = cells[3].inner_text().strip()

                    if not sku_num or not item_name:
                        print("[!] Missing SKU or item name, skipping row.")
                        continue

                    print(f"\n[{row}/{len(rows)}] Processing SKU: {sku_num}")
                    self.navigate_to_sku_page(sku_element, item_name, sku_num)

                except Exception as e:
                    print(f"[!] Error processing row: {e}")

            next_button = self.page.locator('a:has-text(">")')
            if next_button.is_visible() and next_button.is_enabled():
                print("[*] Moving to next page...")
                next_button.click()
                current_page += 1
                time.sleep(8)

            if current_page == PAGE_LIMIT:
                break

    def navigate_to_sku_page(self, sku_element, item_name, sku_num):
        try:
            sku_element.click()
            self.page.wait_for_load_state("networkidle")

            try:
                self.page.wait_for_selector('#ASLoad', state='visible', timeout=5000)
            except:
                print("\n[!] Loading icon not found, continuing...")

            self.page.wait_for_selector('#ASLoad', state='hidden', timeout=15000)
            self.page.wait_for_selector('img[id="ItemPictureHolder"]', state='attached', timeout=15000)
            self.extract_image(item_name, sku_num)

            back_button = self.page.locator('i.fa.fa-chevron-left')
            if back_button.is_visible():
                back_button.click()
                self.page.wait_for_load_state("networkidle")
                self.page.wait_for_selector('table[style="width:max-content;min-width:100%"]', timeout=15000)

        except Exception as e:
            print(f"[!] Failed to open SKU page for {item_name}: {e}")

    def get_image_hash(self, data_url: str) -> str:
        if not data_url.startswith("data:image"):
            return ""
        encoded = data_url.split(",", 1)[1]
        return hashlib.md5(encoded.encode()).hexdigest()

    def extract_image(self, item_name, sku_num):
        try:
            image_locator = self.page.locator('img[id="ItemPictureHolder"]')
            image_src = image_locator.get_attribute("src") or ""
            if not image_src.strip():
                print(f"[!] No image found for {item_name}")
                self.blank_images.append(item_name)
                self.write_to_txt(item_name, sku_num)
                return

            img_hash = self.get_image_hash(image_src)

            if img_hash in self.seen_hashes:
                filename = self.image_hash_map[img_hash]
                print(f"[~] Duplicate image detected, using {filename}")
                img_path = os.path.join(self.output_dir, filename)
            else:
                filename = self.generate_filename(item_name)
                img_path = self.download_image(image_src, filename)
                if img_path:
                    self.seen_hashes.add(img_hash)
                    self.image_hash_map[img_hash] = filename

            self.write_to_csv(sku_num, img_path)
        except Exception as e:
            print(f"[!] Error extracting image for {item_name}: {e}")

    def generate_filename(self, item_name: str) -> str:
        safe_name = item_name.strip().replace(" ", "-")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in "-_")
        return f"{safe_name}.jpg"

    def download_image(self, url: str, filename: str):
        try:
            path = os.path.join(self.output_dir, filename)
            if not url.startswith("data:image"):
                print(f"[!] Not a valid base64 image: {url[:30]}...")
                return None
            encoded = url.split(",", 1)[1]
            data = base64.b64decode(encoded)
            with open(path, 'wb') as f:
                f.write(data)
            print(f"[+] Saved image as: {filename}")
            return path
        except Exception as e:
            print(f"[!] Error saving image: {e}")
        return None

    def create_txt(self, file_path: str = "no_images.txt"):
        try:
            self.blank_txt_path = file_path
            with open(self.blank_txt_path, "a") as f:
                f.write("Items with no image:\n")
            print(f"[+] Created blank image log file: {self.blank_txt_path}")
        except Exception as e:
            print(f"[!] Failed to create TXT file: {e}")

    def create_csv(self, file_path: str = "meta.csv"):
        try:
            self.blank_csv_path = file_path
            with open(self.blank_csv_path, "a") as f:
                f.write("sku,img_src\n")
            print(f"[+] Created csv file: {self.blank_csv_path}")
        except Exception as e:
            print(f"[!] Failed to create CSV file: {e}")

    def write_to_csv(self, sku, img_src):
        try:
            with open(self.blank_csv_path, "a") as f:
                f.write(f"{sku},{img_src}\n")
        except Exception as e:
            print(f"[!] Failed to write to CSV file: {e}")

    def write_to_txt(self, item_name: str, sku_num):
        try:
            with open(self.blank_txt_path, "a") as f:
                f.write(f" - {item_name} | SKU: {sku_num}\n")
        except Exception as e:
            print(f"[!] Failed to write to TXT file: {e}")

    def wait_for_user(self):
        input("[⏸] Paused before scraping. Navigate to the page you want, then press ENTER to start...")

    def run(self, headless=True):
        try:
            self.create_txt()
            self.create_csv()
            self.scrape_database()
            print(f"\n[✔] Process complete! Downloaded {len(self.image_data)} images to '{self.output_dir}'")
            print(f"\n Images not collected: {len(self.blank_images)}")
            print("\nItems with blank images: ")
            for i in self.blank_images:
                print(f"\n - {i}")
        except Exception as e:
            print(f"[!] Error during execution: {e}")
            raise
