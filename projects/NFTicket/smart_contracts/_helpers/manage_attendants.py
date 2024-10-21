# manage_attendants.py

import os
import sys
from algosdk import account, mnemonic
from algosdk.v2client import algod
from algosdk.transaction import ApplicationNoOpTxn, ApplicationOptInTxn
from dotenv import load_dotenv

# Tải biến môi trường từ file .env
load_dotenv()

ALGOD_ADDRESS = os.getenv('NODELY_ENDPOINT_URL')
ALGOD_TOKEN = os.getenv('NODELY_API_KEY')
MNEMONIC = os.getenv('PRIVATE_KEY')
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

def opt_in_app(app_id):
    try:
        # Lấy thông số giao dịch
        params = client.suggested_params()

        # Tạo giao dịch opt-in
        txn = ApplicationOptInTxn(sender_address, params, app_id)

        # Ký giao dịch
        signed_txn = txn.sign(PRIVATE_KEY)

        # Gửi giao dịch
        txid = client.send_transaction(signed_txn)
        print(f"Giao dịch opt-in được gửi với ID: {txid}")

        # Chờ xác nhận
        confirmed_txn = wait_for_confirmation(client, txid, 10)
        print(f"Giao dịch opt-in đã được xác nhận ở round {confirmed_txn.get('confirmed-round')}")
        print("Opt-in thành công vào ứng dụng.")

    except Exception as e:
        print(f"Error opting into app: {e}")

def register_attendant(app_id, event_id):
    try:
        # Lấy thông số giao dịch
        params = client.suggested_params()

        # Chuẩn bị argument cho transaction dưới dạng byte strings
        app_args = [
            "add_attendant".encode('utf-8'),
            event_id.to_bytes(8, 'big')
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
        print("Đã đăng ký tham gia sự kiện thành công.")

    except Exception as e:
        print(f"Error registering attendant: {e}")

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
    # Kiểm tra xem người dùng đã opt-in chưa
    opt_in_app(APP_ID)
    
    # Đăng ký tham gia sự kiện sau khi opt-in
    event_id = 1  # ID của sự kiện
    register_attendant(APP_ID, event_id)