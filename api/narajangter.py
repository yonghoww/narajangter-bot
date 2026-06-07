import asyncio
import httpx
from urllib.parse import unquote
from datetime import datetime, timedelta
from config import API_BASE_URL, NARAJANGTER_API_KEY, CATEGORY_ENDPOINTS, RESULTS_PER_PAGE

_API_KEY = unquote(NARAJANGTER_API_KEY or "")


def _date_range():
    now = datetime.now()
    start = now - timedelta(days=30)
    return start.strftime("%Y%m%d0000"), now.strftime("%Y%m%d2359")


def _is_open(item: dict) -> bool:
    """입찰 마감 전이고 취소공고가 아닌 공고만 통과."""
    if item.get("ntceKindNm", "") == "취소공고":
        return False
    close_dt = item.get("bidClseDt", "")
    if not close_dt:
        return True
    try:
        dt = datetime.strptime(close_dt, "%Y-%m-%d %H:%M:%S")
        return dt >= datetime.now()
    except ValueError:
        return True


async def _fetch_endpoint(client: httpx.AsyncClient, endpoint: str, keyword: str, page: int) -> tuple[list, int]:
    url = f"{API_BASE_URL}/{endpoint}"
    bgn, end = _date_range()
    params = {
        "serviceKey": _API_KEY,
        "type": "json",
        "numOfRows": 100,
        "pageNo": page,
        "inqryDiv": "1",
        "inqryBgnDt": bgn,
        "inqryEndDt": end,
        "bidNtceNm": keyword,
    }
    try:
        resp = await client.get(url, params=params, timeout=20.0)
        resp.raise_for_status()
        body = resp.json().get("response", {}).get("body", {})
        total = int(body.get("totalCount") or 0)
        items = body.get("items", [])
        if isinstance(items, dict):
            raw = items.get("item", [])
            if isinstance(raw, dict):
                raw = [raw]
        elif isinstance(items, list):
            raw = items
        else:
            raw = []
        return raw, total
    except Exception:
        return [], 0


async def search_bids(keyword: str, category: str = "전체", page: int = 1) -> dict:
    endpoints = (
        [CATEGORY_ENDPOINTS[category]]
        if category != "전체"
        else [ep for ep in CATEGORY_ENDPOINTS.values() if ep]
    )

    all_items = []
    async with httpx.AsyncClient(timeout=20.0) as client:
        # 첫 페이지 병렬 요청
        first_results = await asyncio.gather(
            *[_fetch_endpoint(client, ep, keyword, 1) for ep in endpoints]
        )

        extra_tasks = []
        for (items, total), ep in zip(first_results, endpoints):
            filtered = [i for i in items if _is_open(i)]
            all_items.extend(filtered)
            # 추가 페이지가 있으면 수집
            import math
            pages = min(math.ceil(total / 100), 5)
            for p in range(2, pages + 1):
                extra_tasks.append(_fetch_endpoint(client, ep, keyword, p))

        if extra_tasks:
            extra_results = await asyncio.gather(*extra_tasks)
            for items, _ in extra_results:
                all_items.extend(i for i in items if _is_open(i))

    total = len(all_items)
    start = (page - 1) * RESULTS_PER_PAGE
    paged = all_items[start: start + RESULTS_PER_PAGE]

    return {
        "items": paged,
        "total": total,
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
        ("낙찰방법", item.get("cntrctCnclsMthdNm", "-")),
        ("추정가격", format_price(item.get("presmptPrce", ""))),
        ("공고일시", item.get("bidNtceDt", "-")),
        ("마감일시", item.get("bidClseDt", "-")),
        ("개찰일시", item.get("opengDt", "-")),
    ]
    text = "\n".join(f"*{k}:* {v}" for k, v in fields)
    url = item.get("ntceSpecDocUrl1", "")
    if url:
        text += f"\n\n[공고문서 바로가기]({url})"
    return text
