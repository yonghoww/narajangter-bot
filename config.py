import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
NARAJANGTER_API_KEY = os.getenv("DATA_API_KEY")

API_BASE_URL = "https://apis.data.go.kr/1230000/BidPublicInfoService04"

CATEGORY_ENDPOINTS = {
    "전체": None,
    "물품": "getBidPblancListInfoThng01",
    "공사": "getBidPblancListInfoCnstwk01",
    "서비스": "getBidPblancListInfoServc01",
    "기타": "getBidPblancListInfoEtc01",
}

RESULTS_PER_PAGE = 5
