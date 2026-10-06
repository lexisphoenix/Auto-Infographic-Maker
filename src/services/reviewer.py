import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.models import InfographicItem

logger = logging.getLogger(__name__)

class TelegramReviewer:
    def __init__(self, bot_token: str, chat_id: str, queue_manager):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.queue = queue_manager

    async def send_for_review(self, item: InfographicItem) -> None:
        keyboard = [
            [InlineKeyboardButton("Approve", callback_data=f"approve_{item.id}")],
            [InlineKeyboardButton("Schedule", callback_data=f"schedule_{item.id}")],
            [InlineKeyboardButton("Edit Caption", callback_data=f"edit_caption_{item.id}")],
            [InlineKeyboardButton("Regenerate", callback_data=f"regenerate_{item.id}")],
            [InlineKeyboardButton("Reject", callback_data=f"reject_{item.id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        caption = f"New Infographic for Review!\nTitle: {item.title}\n\n{item.caption}"
        logger.info(f"Would send item {item.id} to Telegram for review.")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data
        
        action, item_id = data.split("_", 1)
        if action == "approve":
            await self.queue.update_status(item_id, "approved")
            await query.edit_message_caption(caption=f"Approved!")
        elif action == "reject":
            await self.queue.update_status(item_id, "rejected")
            await query.edit_message_caption(caption=f"Rejected.")
