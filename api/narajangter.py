import httpx
from config import API_BASE_URL, NARAJANGTER_API_KEY, CATEGORY_ENDPOINTS, RESULTS_PER_PAGE


async def search_bids(keyword: str, category: str = "전체", page: int = 1) -> dict:
    """나라장터 입찰공고 검색. 결과: {"items": [...], "total": int, "page": int}"""
    endpoints = (
        [CATEGORY_ENDPOINTS[category]]
        if category != "전체"
        else [ep for ep in CATEGORY_ENDPOINTS.values() if ep]
    )

    all_items = []
    total_count = 0

    params = {
        "serviceKey": NARAJANGTER_API_KEY,
        "_type": "json",
        "numOfRows": 20,
        "pageNo": page,
        "bidNtceNm": keyword,
        "cntrctCnclsMthdNm": "일반경쟁",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        for endpoint in endpoints:
            url = f"{API_BASE_URL}/{endpoint}"
            try:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                body = data.get("response", {}).get("body", {})
                items = body.get("items", {})
                if isinstance(items, dict):
                    raw = items.get("item", [])
                    if isinstance(raw, dict):
                        raw = [raw]
                    # 일반경쟁이 아닌 결과 제외 (API 파라미터 미지원 시 대비)
                    raw = [i for i in raw if i.get("cntrctCnclsMthdNm", "일반경쟁") == "일반경쟁"]
                    all_items.extend(raw)
                    total_count += int(body.get("totalCount", 0))
            except Exception:
                continue

    return {
        "items": all_items[:RESULTS_PER_PAGE],
        "total": total_count,
        "page": page,
        "keyword": keyword,
        "category": category,
    }


def format_price(price_str: str) -> str:
    try:
        return f"{int(float(price_str)):,}원"
    except (ValueError, TypeError):
        return "미공개"


def format_item_summary(item: dict, index: int) -> str:
    name = item.get("bidNtceNm", "제목 없음")
    org = item.get("ntceInsttNm", "-")
    close_dt = item.get("bidClseDt", "-")
    price = format_price(item.get("presmptPrce", ""))
    return (
        f"*{index}.* {name}\n"
        f"  기관: {org}\n"
        f"  추정가: {price}\n"
        f"  마감: {close_dt}"
    )


def format_item_detail(item: dict) -> str:
    fields = [
        ("공고번호", item.get("bidNtceNo", "-")),
        ("공고명", item.get("bidNtceNm", "-")),
        ("공고기관", item.get("ntceInsttNm", "-")),
        ("수요기관", item.get("dminsttNm", "-")),
        ("추정가격", format_price(item.get("presmptPrce", ""))),
        ("공고일시", item.get("bidNtceDt", "-")),
        ("마감일시", item.get("bidClseDt", "-")),
        ("개찰일시", item.get("opengDt", "-")),
    ]
    text = "\n".join(f"*{k}:* {v}" for k, v in fields)
    url = item.get("ntceSpecFileUrl1", "")
    if url:
        text += f"\n\n[공고문서 바로가기]({url})"
    return text
