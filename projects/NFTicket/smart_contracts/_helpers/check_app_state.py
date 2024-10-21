# check_app_state.py

import os
from algosdk.v2client import algod
from dotenv import load_dotenv
from algosdk import encoding

# Tải biến môi trường từ file .env
load_dotenv()

ALGOD_ADDRESS = os.getenv('NODELY_ENDPOINT_URL')
ALGOD_TOKEN = os.getenv('NODELY_API_KEY')
APP_ID = 724732255  # Thay bằng Application ID của bạn

# Khởi tạo client
client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)

def check_app_state(app_id):
    try:
        app_info = client.application_info(app_id)
        global_state = app_info['params']['global-state']

        # Chuyển đổi global state từ base64
        decoded_state = {}
        for item in global_state:
            key_bytes = encoding.base64.b64decode(item['key'])
            try:
                key_str = key_bytes.decode('utf-8')
            except UnicodeDecodeError:
                key_str = ''.join([chr(b) for b in key_bytes])

            if item['value']['type'] == 1:
                value = item['value']['bytes']
                try:
                    value_int = int.from_bytes(value, byteorder='big')
                    value = value_int
                except:
                    pass  # Giữ nguyên bytes nếu không thể chuyển đổi
            elif item['value']['type'] == 2:
                value = item['value']['uint']
            else:
                value = None

            decoded_state[key_str] = value

        # In ra Global State
        print("Global State của Smart Contract:")
        for k, v in decoded_state.items():
            print(f"{k}: {v}")
        
        # Trả về giá trị event_count (ID của sự kiện gần đây nhất)
        if "event_count" in decoded_state:
            event_count = decoded_state["event_count"]
            print(f"ID của sự kiện mới nhất (event_count): {event_count}")
            return event_count
        else:
            print("event_count không tồn tại trong trạng thái toàn cục.")
            return None

    except Exception as e:
        print(f"Error fetching application info: {e}")
        return None

if __name__ == "__main__":
    check_app_state(APP_ID)