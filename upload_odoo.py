import csv
import base64
import xmlrpc.client
import sys
import os
from configurations.config import settings

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

def update_image(sku, img_path):
    """Find product by SKU and update its image."""
    try:
        # Search for product by default_code (SKU)
        product_ids = models.execute_kw(ODOO_DB, uid, ODOO_API_KEY,
            'product.template', 'search',
            [[['default_code', '=', sku]]]
        )

        if not product_ids:
            print(f"[!] SKU '{sku}' not found in Odoo.")
            return

        product_id = product_ids[0]

        # Check if image file exists
        if not os.path.isfile(img_path):
            print(f"[!] Image file not found for SKU {sku}: {img_path}")
            return

        # Read and encode image
        with open(img_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

        # Update product image
        models.execute_kw(ODOO_DB, uid, ODOO_API_KEY,
            'product.template', 'write',
            [[product_id], {'image_1920': image_data}]
        )

        print(f"[✔] Updated image for SKU '{sku}'.")

    except Exception as e:
        print(f"[!] Error updating SKU '{sku}': {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python upload_images_odoo.py path_to_csv_file")
        sys.exit(1)

    csv_file = sys.argv[1]

    if not os.path.isfile(csv_file):
        print(f"[!] CSV file not found: {csv_file}")
        sys.exit(1)

    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)

        # Skip header row if present
        first_row = next(reader, None)
        if first_row is None:
            print("[!] CSV file is empty.")
            return
            
        # Check if first row is header (contains 'sku' and 'img_src')
        if first_row[0].lower().strip() == 'sku' and first_row[1].lower().strip() == 'img_src':
            # Skip header row
            pass
        else:
            # First row is data, process it
            if len(first_row) >= 2:
                sku, img_path = first_row[0].strip(), first_row[1].strip()
                update_image(sku, img_path)

        # Process remaining rows
        for row in reader:
            if len(row) < 2:
                print(f"[!] Skipping incomplete row: {row}")
                continue
            sku, img_path = row[0].strip(), row[1].strip()
            
            # Skip empty rows
            if not sku or not img_path:
                print(f"[!] Skipping empty SKU or image path: {row}")
                continue
                
            update_image(sku, img_path)

    print("\n[✔] Image upload process complete.")

if __name__ == "__main__":
    main()