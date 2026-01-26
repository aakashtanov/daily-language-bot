from .conversation import *
from .jobs import JOB_NAMES, LanguageEmoji
from .sub_manager import SubManager


class UnsubConversation(BaseConversation):

    def __init__(self, storage: SubManager):
        super().__init__('unsubscribe')
        self.storage = storage


    @conversation_step(-1)
    async def start(self, update: Update, context: CallbackContext):
        current = self.storage.get_subs(update.message.chat_id)
        if len(current) == 0:
            await edit_text(update, 'You have no subscriptions')
            return ConversationHandler.END
        buttons = [[(f'{JOB_NAMES[sub.task]} - {LanguageEmoji[sub.lang]} - {sub.hour}:{sub.minute:02d}', f'task:{sub.task}')] for sub in current]
        buttons.append([('Unsubscribe from all', 'unsub_all')])
        await edit_text(update, 'Choose the task to unsubscribe from', markup=make_choice_keyboard(buttons))
        return 0


    @conversation_step(0, StepTrigger.BUTTON, pattern='^task:')
    async def __handle_unsub_task(self, update: Update, context: CallbackContext):
        query, answer = await get_query(update)
        chat_id = update.callback_query.message.chat_id
        sub = self.storage.remove_sub(chat_id, answer)
        await edit_text(update, f'❌ *Unsubscribed from:* {JOB_NAMES[sub.task]} {LanguageEmoji[sub.lang]}', parse_mode=ParseMode.MARKDOWN)


    @conversation_step(0, StepTrigger.BUTTON, pattern='^unsub_all')
    async def __handle_unsubscribe(self, update: Update, context: CallbackContext):
        chat_id = update.callback_query.message.chat_id
        self.storage.remove_subs(chat_id)
        await edit_text(update, '❌ *Unsubscribed from all tasks*', parse_mode=ParseMode.MARKDOWN)
