# deploy.py

import os
import base64
from algosdk import account, mnemonic
from algosdk.v2client import algod
from algosdk.transaction import ApplicationCreateTxn, StateSchema
from dotenv import load_dotenv

# Tải biến môi trường từ file .env
load_dotenv()

ALGOD_ADDRESS = os.getenv('NODELY_ENDPOINT_URL')
ALGOD_TOKEN = os.getenv('NODELY_API_KEY')
MNEMONIC = os.getenv('PRIVATE_KEY')  # Mnemonic của tài khoản triển khai

# Chuyển mnemonic thành private key
PRIVATE_KEY = mnemonic.to_private_key(MNEMONIC)
sender_address = account.address_from_private_key(PRIVATE_KEY)

# Khởi tạo client
client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)

def compile_program(client, source_code):
    compile_response = client.compile(source_code)
    return base64.b64decode(compile_response['result'])

def deploy_contract():
    with open("approval.teal", "r") as f:
        approval_source = f.read()
    with open("clear_state.teal", "r") as f:
        clear_source = f.read()

    # Biên dịch chương trình
    approval_program = compile_program(client, approval_source)
    clear_program = compile_program(client, clear_source)

    # Định nghĩa trạng thái
    global_schema = StateSchema(num_uints=16, num_byte_slices=0)  # Updated to match new global state variables
    local_schema = StateSchema(num_uints=1, num_byte_slices=0)  # Updated for attendants' local state

    # Lấy thông số giao dịch
    params = client.suggested_params()

    # Tạo giao dịch tạo ứng dụng
    txn = ApplicationCreateTxn(
        sender=sender_address,
        sp=params,
        on_complete=0,  # NoOp
        approval_program=approval_program,
        clear_program=clear_program,
        global_schema=global_schema,
        local_schema=local_schema,
        extra_pages=0
    )

    # Ký giao dịch
    signed_txn = txn.sign(PRIVATE_KEY)

    # Gửi giao dịch
    txid = client.send_transaction(signed_txn)
    print(f"Giao dịch được gửi với ID: {txid}")

    # Chờ xác nhận
    confirmed_txn = wait_for_confirmation(client, txid, 10)
    app_id = confirmed_txn['application-index']
    print(f"Smart contract được triển khai với Application ID: {app_id}")

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
    deploy_contract()