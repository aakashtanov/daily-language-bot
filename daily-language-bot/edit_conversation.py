import re

from .conversation import *
from .jobs import JOB_NAMES, LanguageEmoji
from .sub_manager import SubManager


class EditConversation(BaseConversation):

    def __init__(self, storage: SubManager):
        super().__init__('edit')
        self.storage = storage


    @conversation_step(-1)
    async def start(self, update: Update, context: CallbackContext):
        current = self.storage.get_subs(update.message.chat_id)
        if len(current) == 0:
            await edit_text(update, 'You have no subscriptions')
            return ConversationHandler.END
        buttons = [[(f'{JOB_NAMES[sub.task]} - {LanguageEmoji[sub.lang]} - {sub.hour}:{sub.minute:02d}', f'task:{sub.task}')] for sub in current]
        await edit_text(update, 'Choose the task to edit', markup=make_choice_keyboard(buttons))
        return 0


    @conversation_step(0, StepTrigger.BUTTON, pattern='^task:')
    async def _handle_task(self, update: Update, context: CallbackContext):
        query, answer = await get_query(update)
        context.user_data['task'] = answer
        buttons = [[('📅Schedule', 'setting:schedule'), ('🕕Timezone', 'setting:timezone'), ('🌐Language', 'setting:language')]]
        await edit_text(update, 'Choose the setting to edit', markup=make_choice_keyboard(buttons, only_cancel=True))
        return 1


    @conversation_step(1, StepTrigger.BUTTON, pattern='^setting:')
    async def _handle_setting(self, update: Update, context: CallbackContext):
        pattern = update.callback_query.data
        if pattern == 'setting:schedule':
            await edit_text(update, 'Enter new schedule time in format HH:MM', markup=make_choice_keyboard(only_cancel=True))
            return 2
        elif pattern == 'setting:timezone':
            await edit_text(update, 'Enter new timezone in format +X or -X, where X is timezone hour offset', markup=make_choice_keyboard(only_cancel=True))
            return 3
        elif pattern == 'setting:language':
            buttons = [[('🇩🇪 Deutsch', 'lang:DE'), ('🇬🇧 English', 'lang:EN')]]
            await edit_text(update, 'Choose language', markup=make_choice_keyboard(buttons, only_cancel=True))
            return 4


    @conversation_step(2)
    async def _handle_time(self, update: Update, context: CallbackContext):
        answer = update.message.text
        try:
            pattern = r'^(?P<new_hour>\d\d):(?P<new_minute>\d\d)$'
            match = re.fullmatch(pattern, answer)
            if not match:
                raise ValueError
            data = match.groupdict()
            context.user_data.update(data)
            return self.GO_TO_CONVERSATION_END
        except ValueError as e:
            await edit_text(update, 'Invalid time: expected format HH:MM')
            return 2


    @conversation_step(3)
    async def _handle_timezone(self, update: Update, context: CallbackContext):
        answer = update.message.text
        try:
            if not re.fullmatch(r'^[+-]\d$', answer):
                raise ValueError
            context.user_data['new_timezone'] = int(answer)
            return self.GO_TO_CONVERSATION_END
        except ValueError:
            await edit_text(update, 'Invalid timezone: expected format +X or -X')
            return 2


    @conversation_step(4, StepTrigger.BUTTON, pattern='^lang:')
    async def _handle_language(self, update: Update, context: CallbackContext):
        query, answer = await get_query(update)
        context.user_data['new_lang'] = answer
        return self.GO_TO_CONVERSATION_END


    async def _process_result(self, update: Update, context: CallbackContext):
        chat_id = update.effective_chat.id
        sub = self.storage.remove_sub(chat_id, context.user_data['task'])
        for job in context.job_queue.get_jobs_by_name(f'{context.user_data['task']}_{chat_id}'):
            job.schedule_removal()
        if 'new_hour' in context.user_data:
            sub.hour = int(context.user_data['new_hour'])
            sub.minute = int(context.user_data['new_minute'])
        if 'new_timezone' in context.user_data:
            sub.timezone = int(context.user_data['new_timezone'])
        if 'new_lang' in context.user_data:
            sub.lang = context.user_data['new_lang']
        self.storage.add_sub(chat_id, sub)
        await edit_text(update, f'New settings - {sub.hour}:{sub.minute:02d} GMT{sub.timezone:+} {LanguageEmoji[sub.lang]}')
