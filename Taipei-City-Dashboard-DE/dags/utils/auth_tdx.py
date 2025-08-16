import json
from datetime import datetime, timedelta

import requests
from airflow.models import Variable
from settings.global_config import DATA_PATH, PROXIES

TOKEN_URL = (
    "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
)
HEADERS = {"content-type": "application/x-www-form-urlencoded"}
FILE_NAME = "tdx_token.json"

class TDXAuth:
    """
    The class for authenticating with the 運輸資料流通服務平臺(Transport Data eXchange , TDX) API.
    The class loads the client ID and client secret from the Airflow variables.
    The access token is saved to a file for reuse.
    """

    def __init__(self):
        self.client_id = Variable.get("TDX_CLIENT_ID")
        self.client_secret = Variable.get("TDX_CLIENT_SECRET")
        self.full_file_path = f"{DATA_PATH}/{FILE_NAME}"

    def get_token(self, is_proxy=True, timeout=60):
        """
        Get the access token for authentication.
        This method retrieves the access token from the specified path.
        If the token is not found or has expired, a new token is obtained and saved to the path.

        Args:
            is_proxy (bool): Flag indicating whether to use a proxy. Defaults to True.
            timeout (int): The timeout for the request. Defaults to 60.

        Returns:
            str: The access token.

        Raises:
            FileNotFoundError: If the token file is not found.
            EOFError: If the token file is empty or corrupted.
        """
        # check if the token is expired
        now_time = datetime.now()
        try:
            with open(self.full_file_path, "rb") as handle:
                res = json.load(handle)
                # 確保 JSON 格式正確
                if not isinstance(res, dict) or "access_token" not in res or "expired_time" not in res:
                    raise ValueError("Invalid JSON format: Missing required keys.")
                # 解析時間格式
                expired_time = datetime.fromisoformat(res["expired_time"])
                if now_time < expired_time:  # If the token is not expired
                    return res["access_token"]
        except (FileNotFoundError, EOFError):
            pass

        # get the token
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        try:
            with requests.post(
                TOKEN_URL,
                headers=HEADERS,
                data=data,
                proxies=PROXIES if is_proxy else None,
                timeout=timeout,
            ) as response:
                res_json = response.json()
                token = res_json["access_token"]
                expired_time = now_time + timedelta(seconds=res_json["expires_in"])            
                res = {"access_token": token, "expired_time": expired_time.isoformat()}
                if not isinstance(res_json, dict) or "access_token" not in res_json or "expires_in" not in res_json:
                    raise ValueError("Invalid response format from TDX API.")
                with open(self.full_file_path, "wb") as handle:
                    json.dump(res, handle)
                return token
        except (requests.RequestException, KeyError, ValueError) as e:
            print(e)
            return None