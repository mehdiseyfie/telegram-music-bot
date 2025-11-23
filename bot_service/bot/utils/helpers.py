from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ContextTypes
from logging_config import setup_logging

logger = setup_logging(logstash_host='localhost', logstash_port=5000)

CHANNEL_USERNAME = "@AR_MUSICLAND"
CHANNEL_INVITE_LINK = "https://t.me/AR_MUSICLAND"

async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    try:
        chat_member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return chat_member.status in ['creator', 'administrator', 'member']
    except Exception as e:
        logger.error(f"Error checking membership: {str(e)}")
        return False

async def force_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    logger.debug("Checking subscription")
    is_member = await check_membership(update, context)
    
    if not is_member:
        logger.info("User is not a member of the channel")
        keyboard = [
            [InlineKeyboardButton("عضویت در کانال", url=CHANNEL_INVITE_LINK)],
            [InlineKeyboardButton("بررسی وضعیت عضویت", callback_data="check_join_status")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = "لطفاً برای استفاده از این ربات، در کانال ما عضو شوید:"
        
        if update.message:
            await update.message.reply_text(message, reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
        elif update.inline_query:
            results = [
                InlineQueryResultArticle(
                    id="join_channel",
                    title="برای استفاده از این ربات در کانال ما عضو شوید",
                    description="برای عضویت در کانال کلیک کنید",
                    input_message_content=InputTextMessageContent(message),
                    reply_markup=reply_markup
                )
            ]
            await update.inline_query.answer(results, cache_time=0, is_personal=True)
        return False
    
    logger.debug("User is a member of the channel")
    return True

async def handle_subscription_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    query = update.callback_query
    await query.answer()

    if await check_membership(update, context):
        await query.edit_message_text("ممنون از عضویت شما! اکنون می‌توانید از ربات استفاده کنید.")
        return True
    else:
        keyboard = [
            [InlineKeyboardButton("عضویت در کانال", url=CHANNEL_INVITE_LINK)],
            [InlineKeyboardButton("بررسی مجدد وضعیت عضویت", callback_data="check_join_status")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("شما هنوز عضو کانال نشده‌اید. لطفاً عضو شوید و دوباره امتحان کنید.", reply_markup=reply_markup)
        return False