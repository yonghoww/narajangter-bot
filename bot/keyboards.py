from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import CATEGORY_ENDPOINTS, RESULTS_PER_PAGE


def category_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(cat, callback_data=f"cat:{cat}")
        for cat in CATEGORY_ENDPOINTS.keys()
    ]
    rows = [buttons[:3], buttons[3:]]
    return InlineKeyboardMarkup(rows)


def result_keyboard(items: list, page: int, total: int, keyword: str, category: str) -> InlineKeyboardMarkup:
    rows = []
    for i, item in enumerate(items):
        label = item.get("bidNtceNm", f"공고 {i+1}")
        if len(label) > 40:
            label = label[:38] + "…"
        rows.append([InlineKeyboardButton(label, callback_data=f"detail:{i}")])

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("◀ 이전", callback_data=f"page:{page-1}"))
    if total > page * RESULTS_PER_PAGE:
        nav.append(InlineKeyboardButton("다음 ▶", callback_data=f"page:{page+1}"))
    if nav:
        rows.append(nav)

    rows.append([InlineKeyboardButton("🔍 새 검색", callback_data="new_search")])
    return InlineKeyboardMarkup(rows)


def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀ 목록으로", callback_data="back_to_list")]
    ])
