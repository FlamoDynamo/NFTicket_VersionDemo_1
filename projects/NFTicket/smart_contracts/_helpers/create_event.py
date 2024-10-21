# create_event.py

import os
import sys
from algosdk import account, mnemonic
from algosdk.v2client import algod
from algosdk.transaction import ApplicationNoOpTxn
from dotenv import load_dotenv

# Tải biến môi trường từ file .env
load_dotenv()

ALGOD_ADDRESS = os.getenv('NODELY_ENDPOINT_URL')
ALGOD_TOKEN = os.getenv('NODELY_API_KEY')
MNEMONIC = os.getenv('PRIVATE_KEY')  # Mnemonic của tài khoản triển khai
APP_ID = 724732255  # Application ID mới của bạn

# Chuyển mnemonic thành private key
try:
    PRIVATE_KEY = mnemonic.to_private_key(MNEMONIC)
    sender_address = account.address_from_private_key(PRIVATE_KEY)
except Exception as e:
    print("Error converting mnemonic to private key:", e)
    sys.exit(1)

# Khởi tạo client
client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)

def call_create_event(app_id, nft_id, end_timestamp, ticket_count):
    try:
        # Lấy thông số giao dịch
        params = client.suggested_params()

        # Chuẩn bị argument cho transaction dưới dạng byte strings
        app_args = [
            "create_event".encode('utf-8'),
            nft_id.to_bytes(8, 'big'),
            end_timestamp.to_bytes(8, 'big'),
            ticket_count.to_bytes(8, 'big')
        ]

        # Tạo giao dịch ApplicationNoOp
        txn = ApplicationNoOpTxn(sender_address, params, app_id, app_args)

        # Ký giao dịch
        signed_txn = txn.sign(PRIVATE_KEY)

        # Gửi giao dịch
        txid = client.send_transaction(signed_txn)
        print(f"Giao dịch được gửi với ID: {txid}")

        # Chờ xác nhận
        confirmed_txn = wait_for_confirmation(client, txid, 10)
        print(f"Giao dịch đã được xác nhận ở round {confirmed_txn.get('confirmed-round')}")
        print("Sự kiện mới đã được tạo thành công.")

    except Exception as e:
        print(f"Error creating event: {e}")

def wait_for_confirmation(client, txid, timeout):
    import time
    try:
        last_round = client.status().get('last-round')
    except Exception as e:
        print("Error getting status:", e)
        return
    current_round = last_round + 1

    while current_round < last_round + timeout:
        try:
            pending_txn = client.pending_transaction_info(txid)
            if pending_txn.get('confirmed-round', 0) > 0:
                return pending_txn
            elif pending_txn.get('pool-error'):
                raise Exception(f"Lỗi Pool: {pending_txn.get('pool-error')}")
        except Exception as e:
            print(e)
            return

        print(f"Đang chờ xác nhận... Block hiện tại: {current_round}")
        time.sleep(1)
        current_round += 1

    raise Exception("Timeout chờ xác nhận giao dịch")

if __name__ == "__main__":
    nft_id = 15890685  # Thay bằng NFT ID thực tế
    end_timestamp = 1729580400  # Thay bằng timestamp thực tế
    ticket_count = 100  # Số lượng vé cho sự kiện
    call_create_event(APP_ID, nft_id, end_timestamp, ticket_count)