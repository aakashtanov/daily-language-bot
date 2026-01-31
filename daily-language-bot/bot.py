import logging
import pathlib
from types import SimpleNamespace

from telegram import Update, BotCommand, MenuButtonCommands
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters, CallbackContext,
)

from .sub_manager import SubManager, SubInfo
from .checks import dispatch_check
from .jobs import *
from .subscribe_conversation import SubConversation
from .unsubscibe_conversation import UnsubConversation
from .edit_conversation import EditConversation

logger = logging.getLogger(__name__)


class Bot:

    __CMDS = {
        'subscribe': 'Subscribe to tasks',
        'unsubscribe': 'Unsubscribe from tasks',
        'list': 'List current subscriptions',
        'edit': 'Edit time of subscriptions'
    }


    def __init__(self, data_dir: str):
        with open(pathlib.Path(data_dir) / 'token', 'r', encoding='utf-8') as f:
            self.app = ApplicationBuilder().token(f.read().strip()).post_init(self.__post_init).build()
        self.data_dir = data_dir
        self.sub_manager = SubManager(pathlib.Path(data_dir), self.app)
        self._init_cmds()


    async def __post_init(self, app):
        await app.bot.set_my_commands([BotCommand(cmd, desc) for cmd, desc in self.__CMDS.items()])
        await app.bot.set_chat_menu_button(menu_button=MenuButtonCommands())


    def run(self):
        logger.info(f'Starting bot')
        self.app.run_polling()


    def _init_cmds(self):
        self.app.add_handler(SubConversation(self.sub_manager))
        self.app.add_handler(UnsubConversation(self.sub_manager))
        self.app.add_handler(EditConversation(self.sub_manager))
        self.app.add_handler(CommandHandler('list', self._list))
        self.app.add_handler(CommandHandler('test', self._test))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, dispatch_check))


    async def _list(self, update: Update, context: CallbackContext):
        chat_id = update.message.chat_id
        subs = self.sub_manager.get_subs(chat_id)
        if len(subs) == 0:
            await update.message.reply_text('You have no subscriptions')
            return

        msg = 'You are currently subscribed to:\n\n'
        for sub in subs:
            msg += f'{JOB_NAMES[sub.task]} - {LanguageEmoji[sub.lang]} - {sub.hour}:{sub.minute:02d} GMT{sub.timezone:+}\n'
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


    async def _test(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        logger.info(f'Testing in chat {chat_id}')
        tokens = update.message.text.split()
        if len(tokens) == 3:
            task = tokens[1]
            language = tokens[2].upper()
        elif len(tokens) == 2:
            task = tokens[1]
            language = 'DE'
        else:
            await update.message.reply_text('Task not specified')
            return

        if task not in JobTypes:
            await update.message.reply_text('Invalid task')
            return

        fake_job = SimpleNamespace(chat_id=chat_id, data={'data_dir': self.data_dir, 'language': language})
        fake_context = SimpleNamespace(
            bot=context.bot,
            bot_data=context.bot_data,
            job=fake_job,
        )

        await self.sub_manager.JOBS[JobTypes(task)](fake_context)
