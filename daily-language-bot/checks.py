import logging

from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram import Update

from .jobs import DAILY_NUMBERS_BATCH_SIZE
from .numbers_de import NUMBERS


logger = logging.getLogger(__name__)


async def dispatch_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    logger.debug(f'Received answer from {chat_id}: {update.message.text}')
    expected = context.bot_data.get(chat_id)
    if not expected:
        logger.warning(f'No active exercise for chat {chat_id}')
        await update.message.reply_text('No active exercise for this chat')
        return

    if expected['task'] == 'numbers':
        await check_numbers_task(update, chat_id, expected)
    else:
        await update.message.reply_text('Unsupported task')


async def check_numbers_task(update: Update, chat_id, expected: dict):
    language = expected['language']
    answers = update.message.text.lower().split()
    if len(answers) < DAILY_NUMBERS_BATCH_SIZE * 3:
        logger.info(f'Invalid answer length ({len(answers)}) from {chat_id}')
        await update.message.reply_text(f'❌ Please send {DAILY_NUMBERS_BATCH_SIZE * 3} answers.')
        return

    score = 0
    score_message = ''

    # First 10 – Numbers to german text
    score_message += '🔢 *Numbers*\n'
    for ans, num in zip(answers[:DAILY_NUMBERS_BATCH_SIZE], expected['numerical']):
        correct: bool = ans == NUMBERS[language][num]
        score_message += '✅' if correct else '❌'
        score_message += f' {num} - {NUMBERS[language][num]}\n'
        if correct:
            score += 1
    score_message += '\n'

    # Second 10 – German text to numbers
    score_message += '📝 *Text Numbers*\n'
    for ans, num in zip(answers[DAILY_NUMBERS_BATCH_SIZE:DAILY_NUMBERS_BATCH_SIZE * 2], expected['text']):
        correct: bool = ans.isdigit() and int(ans) == num
        score_message += '✅' if correct else '❌'
        score_message += f' {NUMBERS[language][num]} - {num}\n'
        if correct:
            score += 1
    score_message += '\n'

    # Third 10 – Numbers from audio
    score_message += '🔊 *Audio Numbers*\n'
    for ans, num in zip(answers[DAILY_NUMBERS_BATCH_SIZE * 2:], expected['audio']):
        correct: bool = ans.isdigit() and int(ans) == num
        score_message += '✅' if correct else '❌'
        score_message += f' {NUMBERS[language][num]} - {num}\n'
        if correct:
            score += 1
    score_message += '\n'

    score_message += f'Total score : {score}/{DAILY_NUMBERS_BATCH_SIZE * 3}'

    logger.info(f'User {chat_id} scored {score}/{DAILY_NUMBERS_BATCH_SIZE * 3}')
    await update.message.reply_text(score_message, parse_mode=ParseMode.MARKDOWN)