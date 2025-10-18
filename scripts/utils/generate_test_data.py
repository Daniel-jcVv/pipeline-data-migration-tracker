"""
Generate test CSV files and upload directly to SFTP server.

Usage:
    python scripts/utils/generate_test_data.py --files 5 --rows 100
"""
import csv
import random
import argparse
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import paramiko
import config


def generate_order_data(num_rows=100):
    """Generate order data matching existing format."""
    regions = ['NORTH', 'SOUTH', 'EAST', 'WEST']
    data = []

    # Random date in 2024
    start_date = datetime(2024, 1, 1)

    for i in range(num_rows):
        order_id = f"ORD_{i:06d}"
        customer_id = f"CUST_{random.randint(0, 99):05d}"

        # Random date
        days_offset = random.randint(0, 365)
        order_date = (start_date + timedelta(days=days_offset)).strftime('%Y-%m-%d')

        region = random.choice(regions)
        product_id = f"PROD_{random.randint(1, 50):03d}"
        quantity = random.randint(1, 100)
        unit_price = round(random.uniform(10.0, 1000.0), 2)
        total_amount = round(quantity * unit_price, 2)

        data.append({
            'order_id': order_id,
            'customer_id': customer_id,
            'order_date': order_date,
            'region': region,
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'total_amount': total_amount
        })

    return data


def write_csv(data, filename):
    """Write data to CSV file."""
    fieldnames = ['order_id', 'customer_id', 'order_date', 'region',
                  'product_id', 'quantity', 'unit_price', 'total_amount']

    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    print(f"Created: {filename} ({len(data)} rows)")


def upload_to_sftp(local_file, remote_filename):
    """Upload file directly to SFTP server."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=config.SFTP_HOST,
        port=config.SFTP_PORT,
        username=config.SFTP_USERNAME,
        password=config.SFTP_PASSWORD
    )
    sftp = ssh.open_sftp()

    remote_path = f"{config.SFTP_SERVER_PATH}/{remote_filename}"
    sftp.put(local_file, remote_path)

    sftp.close()
    ssh.close()
    print(f"  ✅ Uploaded to SFTP: {remote_path}")


def main():
    parser = argparse.ArgumentParser(description='Generate test CSV files and upload to SFTP')
    parser.add_argument('--files', type=int, default=2,
                        help='Number of CSV files to generate (default: 2)')
    parser.add_argument('--rows', type=int, default=100,
                        help='Number of rows per file (default: 100)')

    args = parser.parse_args()

    print(f"Generating {args.files} CSV files with {args.rows} rows each...")
    print(f"Uploading directly to SFTP: {config.SFTP_HOST}:{config.SFTP_SERVER_PATH}")
    print("=" * 77)

    for i in range(args.files):
        # Generate filename
        filename = f"orders_2024_test_{i+1:02d}.csv"

        # Generate data
        data = generate_order_data(args.rows)

        # Write to temp file
        with tempfile.NamedTemporaryFile(mode='w', newline='', delete=False, suffix='.csv') as tmp:
            fieldnames = ['order_id', 'customer_id', 'order_date', 'region',
                          'product_id', 'quantity', 'unit_price', 'total_amount']
            writer = csv.DictWriter(tmp, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
            tmp_path = tmp.name

        # Upload to SFTP
        try:
            upload_to_sftp(tmp_path, filename)
        except Exception as e:
            print(f"  ❌ Upload failed: {e}")
        finally:
            Path(tmp_path).unlink()  # Delete temp file

    print("=" * 77)
    print(f"✅ Generated and uploaded {args.files} test files to SFTP server")


if __name__ == "__main__":
    main()
