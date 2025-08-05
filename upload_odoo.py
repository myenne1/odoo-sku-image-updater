import csv
import base64
import xmlrpc.client
import sys
import os
import time
from datetime import datetime
from configurations.config import settings
from datetime import UTC

ODOO_DB = settings.ODOO_DB
ODOO_URL = settings.ODOO_URL
ODOO_USERNAME = settings.ODOO_USERNAME
ODOO_API_KEY = settings.ODOO_API_KEY

common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_API_KEY, {})
if not uid:
    print("[!] Authentication failed. Check credentials.")
    sys.exit(1)

models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")

success_log = []
failure_log = []
checkpoint_file = "last_checkpoint.txt"


def get_last_checkpoint():
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r') as f:
            return f.read().strip()
    return None


def update_checkpoint(sku):
    with open(checkpoint_file, 'w') as f:
        f.write(sku)


def update_image(sku, img_path):
    try:
        product_ids = models.execute_kw(ODOO_DB, uid, ODOO_API_KEY,
            'product.template', 'search',
            [[['default_code', '=', sku]]]
        )

        if not product_ids:
            msg = f"SKU '{sku}' not found in Odoo."
            failure_log.append((sku, img_path, msg))
            return

        product_id = product_ids[0]

        if not os.path.isfile(img_path):
            msg = f"Image not found: {img_path}"
            failure_log.append((sku, img_path, msg))
            return

        if not img_path.lower().endswith(('.jpg', '.jpeg', '.png')):
            msg = f"Unsupported format: {img_path}"
            failure_log.append((sku, img_path, msg))
            return

        if os.path.getsize(img_path) > 2 * 1024 * 1024:
            msg = f"Image too large (>2MB): {img_path}"
            failure_log.append((sku, img_path, msg))
            return

        with open(img_path, 'rb') as f:
            image_bytes = f.read()
            checksum = hash(image_bytes)
            image_data = base64.b64encode(image_bytes).decode('utf-8')

        models.execute_kw(ODOO_DB, uid, ODOO_API_KEY,
            'product.template', 'write',
            [[product_id], {'image_1920': image_data}]
        )

        success_log.append((sku, img_path, checksum))
        update_checkpoint(sku)

    except Exception as e:
        failure_log.append((sku, img_path, str(e)))


def estimate_time(start_time, current, total):
    elapsed = time.time() - start_time
    rate = elapsed / current if current else 1
    remaining = rate * (total - current)
    return str(datetime.fromtimestamp(remaining, UTC).strftime("%H:%M:%S"))


def main():
    if len(sys.argv) != 2:
        print("Usage: python upload_images_odoo.py path_to_csv_file")
        sys.exit(1)

    csv_file = sys.argv[1]
    if not os.path.isfile(csv_file):
        print(f"[!] CSV file not found: {csv_file}")
        sys.exit(1)

    last_checkpoint = get_last_checkpoint()
    started = False if last_checkpoint else True

    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
        if rows and rows[0][0].lower().strip() == 'sku':
            rows = rows[1:]

        total = len(rows)
        start_time = time.time()

        for i, row in enumerate(rows):
            if len(row) < 2:
                continue

            sku, img_path = row[0].strip(), row[1].strip()
            if not sku or not img_path:
                continue

            if not started:
                if sku == last_checkpoint:
                    started = True
                continue

            print(f"[*] Uploading {i+1}/{total}: {sku} ... ETA: {estimate_time(start_time, i+1, total)}")
            update_image(sku, img_path)

    generate_report()


def generate_report(report_path="upload_report.txt"):
    with open(report_path, "w") as f:
        f.write("UPLOAD REPORT\n")
        f.write("=" * 60 + "\n\n")

        f.write("✔ SUCCESSFUL UPLOADS\n")
        f.write("-" * 60 + "\n")
        f.write(f"{'SKU':<20} {'Image Path':<30} {'Checksum':<10}\n")
        f.write("-" * 60 + "\n")
        for sku, path, checksum in success_log:
            f.write(f"{sku:<20} {os.path.basename(path):<30} {checksum}\n")
        if not success_log:
            f.write("[None]\n")

        f.write("\n✖ FAILED UPLOADS\n")
        f.write("-" * 60 + "\n")
        f.write(f"{'SKU':<20} {'Image Path':<30} {'Error'}\n")
        f.write("-" * 60 + "\n")
        for sku, path, error in failure_log:
            f.write(f"{sku:<20} {os.path.basename(path):<30} {error}\n")
        if not failure_log:
            f.write("[None]\n")

    print(f"[*] Report saved to: {report_path}")


if __name__ == "__main__":
    main()
