import os
from pathlib import Path
# use cwa 
from dotenv import load_dotenv
import requests

load_dotenv()  # take environment variables
root_dir = Path(__file__).parent.parent.parent.parent
load_dotenv(root_dir / ".env")

CWA_TOKEN = os.getenv("CWA_TOKEN")
print(CWA_TOKEN)

# url -X 'GET' \
#   'https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0005-001?Authorization=CWA-80313285-2296-4E79-BA46-38D693D6DA4D' \
#   -H 'accept: application/json'

resp = requests.get(
    # "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization=CWA-80313285-2296-4E79-BA46-38D693D6DA4D&format=JSON&WeatherElement=UVIndex"
    "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001",
    params={
		"Authorization": CWA_TOKEN,
		"format": "JSON",
		"WeatherElement": "UVIndex",
	}
)
print(resp)

with open("uv.json", "w") as f:
    f.write(resp.text)
    

