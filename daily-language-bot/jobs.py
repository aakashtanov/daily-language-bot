import logging
import random
import os
import pathlib
from enum import StrEnum

from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram import InputFile

from .numbers_de import NUMBERS
from .audio import generate_voice_track, get_duration

DAILY_NUMBERS_BATCH_SIZE = 3



logger = logging.getLogger(__name__)


class JobTypes(StrEnum):
    NUMBERS = 'numbers'
    VERBS = 'verbs'


JOB_NAMES = {
    JobTypes.NUMBERS.value: '📘 Daily numbers',
    JobTypes.VERBS.value: '📖 Irregular verbs'
}

LanguageEmoji = {
    'EN': '🇬🇧',
    'DE': '🇩🇪'
}


async def send_daily_numbers(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    language = context.job.data['language']
    logger.info(f'Sending daily numbers to chat {chat_id}')

    nums = random.sample(range(1, 100), DAILY_NUMBERS_BATCH_SIZE * 3)
    nums_numerical, nums_text, nums_audio = (nums[:DAILY_NUMBERS_BATCH_SIZE],
                                             nums[DAILY_NUMBERS_BATCH_SIZE:DAILY_NUMBERS_BATCH_SIZE * 2],
                                             nums[DAILY_NUMBERS_BATCH_SIZE * 2:])

    context.bot_data[chat_id] = {
        'task':      'numbers',
        'language':  language,
        'numerical': nums_numerical,
        'text':      nums_text,
        'audio':     nums_audio,
    }

    message = (
       f'📘{LanguageEmoji[language]} *Daily Numbers*\n\n'
        '🔢 *Numbers (translate)*\n' + '  '.join(map(str, nums_numerical)) + '\n\n' +
        '📝 *Text Numbers*\n\n' + '\n'.join(NUMBERS[language][n] for n in nums_text) + '\n\n' +
        '🔊 *Audio Numbers*\n'
        '(see audio message below)'
    )

    await context.bot.send_message(chat_id, message, parse_mode=ParseMode.MARKDOWN)

    audio_dir = os.path.join(context.job.data['data_dir'], 'audio')
    audio_track_file = generate_voice_track([NUMBERS[language][n] for n in nums_audio], audio_dir=audio_dir, out_name='daily_numbers.ogg', lang=language.lower())
    audio_file = open(audio_track_file, 'rb')
    await context.bot.send_voice(
        chat_id,
        InputFile(audio_file, filename='daily_numbers.ogg'),
        duration=get_duration(audio_track_file),
        disable_notification=True
    )


async def send_daily_verbs(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    language = context.job.data['language']
    logger.info(f'Sending daily verbs to chat {chat_id}')

    with open(pathlib.Path(context.job.data['data_dir']) / f'verbs_{language.lower()}.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        todays = lines[random.randint(0, len(lines))].split(';')
        verb = todays[0]
        verb_forms = todays[:3]
        translation = todays[3]

    message = (
        f'📖{LanguageEmoji[language]} <b>Daily Irregular verbs</b>\n\n'
        f'<b>{verb}</b> - <tg-spoiler>{translation}</tg-spoiler>\n'
        f'Forms: <tg-spoiler><b>{verb_forms[0]} - {verb_forms[1]} - {verb_forms[2]}</b></tg-spoiler>'
    )

    await context.bot.send_message(chat_id, message, parse_mode=ParseMode.HTML)
    audio_dir = os.path.join(context.job.data['data_dir'], 'audio')
    audio_track_file = generate_voice_track(verb_forms, audio_dir=audio_dir, out_name='daily_numbers.ogg', lang=language)
    audio_file = open(audio_track_file, 'rb')
    await context.bot.send_voice(
        chat_id,
        InputFile(audio_file, filename='daily_numbers.ogg'),
        duration=get_duration(audio_track_file),
    )
