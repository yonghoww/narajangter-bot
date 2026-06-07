import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
NARAJANGTER_API_KEY = os.getenv("DATA_API_KEY")

API_BASE_URL = "https://apis.data.go.kr/1230000/ad/BidPublicInfoService"

CATEGORY_ENDPOINTS = {
    "전체": None,
    "물품": "getBidPblancListInfoThngPPSSrch",
    "공사": "getBidPblancListInfoCnstwkPPSSrch",
    "서비스": "getBidPblancListInfoServcPPSSrch",
    "기타": "getBidPblancListInfoFrgcptPPSSrch",
}

RESULTS_PER_PAGE = 5
