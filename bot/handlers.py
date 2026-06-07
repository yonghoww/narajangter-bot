import logging
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from telegram.constants import ParseMode

from api.narajangter import search_bids, format_item_summary, format_item_detail
from bot.keyboards import category_keyboard, result_keyboard, back_keyboard

logger = logging.getLogger(__name__)

CATEGORY, KEYWORD = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "안녕하세요! *나라장터 입찰공고 검색 봇*입니다.\n\n"
        "• /search — 입찰공고 검색\n"
        "• /help — 도움말\n\n"
        "또는 키워드를 바로 입력하면 전체 업종에서 검색합니다.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "*사용 방법*\n\n"
        "1. /search 입력 후 업종 선택 → 키워드 입력\n"
        "2. 또는 검색할 키워드를 바로 메시지로 입력\n\n"
        "*결과 화면*\n"
        "• 공고 제목 버튼 → 상세 정보\n"
        "• 이전/다음 버튼 → 페이지 이동\n"
        "• 새 검색 버튼 → 처음부터 다시",
        parse_mode=ParseMode.MARKDOWN,
    )


async def search_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "어떤 업종을 검색할까요?",
        reply_markup=category_keyboard(),
    )
    return CATEGORY


async def category_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    category = query.data.split(":", 1)[1]
    context.user_data["category"] = category
    await query.edit_message_text(f"*{category}* 업종을 선택했습니다.\n\n검색할 키워드를 입력해주세요.", parse_mode=ParseMode.MARKDOWN)
    return KEYWORD


async def keyword_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyword = update.message.text.strip()
    category = context.user_data.get("category", "전체")
    await _do_search(update, context, keyword, category, page=1)
    return ConversationHandler.END


async def direct_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyword = update.message.text.strip()
    await _do_search(update, context, keyword, "전체", page=1)


async def _do_search(update: Update, context: ContextTypes.DEFAULT_TYPE, keyword: str, category: str, page: int) -> None:
    msg = update.message or (update.callback_query and update.callback_query.message)
    status = await msg.reply_text("🔍 검색 중...")

    result = await search_bids(keyword, category, page)
    items = result["items"]
    total = result["total"]

    context.user_data["search"] = result

    await status.delete()

    if not items:
        await msg.reply_text(f"*'{keyword}'* 검색 결과가 없습니다.", parse_mode=ParseMode.MARKDOWN)
        return

    text = f"*'{keyword}'* 검색 결과 (총 {total}건, {page}페이지)\n\n"
    text += "\n\n".join(format_item_summary(item, i + 1) for i, item in enumerate(items))

    await msg.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=result_keyboard(items, page, total, keyword, category),
    )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "new_search":
        await query.edit_message_reply_markup(None)
        await query.message.reply_text("어떤 업종을 검색할까요?", reply_markup=category_keyboard())
        context.user_data["awaiting_keyword_after_category"] = True

    elif data.startswith("page:"):
        page = int(data.split(":")[1])
        search = context.user_data.get("search", {})
        keyword = search.get("keyword", "")
        category = search.get("category", "전체")
        result = await search_bids(keyword, category, page)
        items = result["items"]
        total = result["total"]
        context.user_data["search"] = result

        text = f"*'{keyword}'* 검색 결과 (총 {total}건, {page}페이지)\n\n"
        text += "\n\n".join(format_item_summary(item, i + 1) for i, item in enumerate(items))
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=result_keyboard(items, page, total, keyword, category),
        )

    elif data.startswith("detail:"):
        idx = int(data.split(":")[1])
        search = context.user_data.get("search", {})
        items = search.get("items", [])
        if idx < len(items):
            await query.edit_message_text(
                format_item_detail(items[idx]),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=back_keyboard(),
                disable_web_page_preview=True,
            )

    elif data == "back_to_list":
        search = context.user_data.get("search", {})
        items = search.get("items", [])
        page = search.get("page", 1)
        total = search.get("total", 0)
        keyword = search.get("keyword", "")
        category = search.get("category", "전체")
        if items:
            text = f"*'{keyword}'* 검색 결과 (총 {total}건, {page}페이지)\n\n"
            text += "\n\n".join(format_item_summary(item, i + 1) for i, item in enumerate(items))
            await query.edit_message_text(
                text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=result_keyboard(items, page, total, keyword, category),
            )

    elif data.startswith("cat:"):
        category = data.split(":", 1)[1]
        context.user_data["category"] = category
        context.user_data["awaiting_keyword_after_category"] = True
        await query.edit_message_text(
            f"*{category}* 업종을 선택했습니다.\n\n검색할 키워드를 입력해주세요.",
            parse_mode=ParseMode.MARKDOWN,
        )


async def any_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get("awaiting_keyword_after_category"):
        context.user_data["awaiting_keyword_after_category"] = False
        keyword = update.message.text.strip()
        category = context.user_data.get("category", "전체")
        await _do_search(update, context, keyword, category, page=1)
    else:
        await direct_search(update, context)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("검색을 취소했습니다.")
    return ConversationHandler.END


def build_handlers():
    conv = ConversationHandler(
        entry_points=[CommandHandler("search", search_start)],
        states={
            CATEGORY: [CallbackQueryHandler(category_chosen, pattern=r"^cat:")],
            KEYWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, keyword_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    return [
        CommandHandler("start", start),
        CommandHandler("help", help_cmd),
        conv,
        CallbackQueryHandler(callback_handler),
        MessageHandler(filters.TEXT & ~filters.COMMAND, any_message),
    ]
