import re

from .conversation import *
from .sub_manager import SubManager, SubInfo
from .jobs import *


class SubConversation(BaseConversation):

    __JOBS = {
        JobTypes.NUMBERS: send_daily_numbers,
        JobTypes.VERBS: send_daily_verbs
    }
    def __init__(self, storage: SubManager):
        super().__init__('subscribe')
        self.storage = storage


    @conversation_step(-1)
    async def start(self, update: Update, context: CallbackContext):
        return await self.__choose_task(update, context)


    async def __choose_task(self, update: Update, context: CallbackContext):
        chat_id = update.message.chat_id
        buttons = [[(job_name, 'task:' + job_desc)] for job_desc, job_name in JOB_NAMES.items()]
        await edit_text(update, 'Select one of available tasks', markup=make_choice_keyboard(buttons, only_cancel=True))
        return 0


    @conversation_step(0, StepTrigger.BUTTON, pattern='^task:')
    async def __handle_task(self, update: Update, context: CallbackContext):
        query, answer = await get_query(update)
        context.user_data['task'] = answer
        buttons = [[('🇩🇪 Deutsch', 'lang:DE'), ('🇬🇧 English', 'lang:EN')]]
        await edit_text(update, 'Select the language for the task', markup=make_choice_keyboard(buttons, only_cancel=True))
        return 1


    @conversation_step(1, StepTrigger.BUTTON, pattern='^lang:')
    async def __handle_lang(self, update: Update, context: CallbackContext):
        query, answer = await get_query(update)
        context.user_data['lang'] = answer
        if self.storage.has_sub(update.callback_query.message.chat_id, context.user_data['task'], context.user_data['lang']):
            await edit_text(update, 'You already have this subscription.\nUse `\\edit` command to change its settings', parse_mode=ParseMode.MARKDOWN)
            return ConversationHandler.END

        buttons = [[('Use default: 12:00 GMT+0', 'time:default')]]
        msg = ('Enter the time for the daily sending in format HH:MM\n'
               'You may indicate the timezone by putting its offset after the time\n'
               'E.g. 13:45+2'
               )
        await edit_text(update, msg, markup=make_choice_keyboard(buttons, only_cancel=True))
        return 2


    @conversation_step(2, StepTrigger.BUTTON, pattern='^time:')
    async def __handle_button_time(self, update: Update, context: CallbackContext):
        # only default 12:00 GMT+0 at the moment
        context.user_data['hour'] = 12
        context.user_data['minute'] = 0
        context.user_data['timezone'] = 0


    @conversation_step(2)
    async def _handle_time(self, update: Update, context: CallbackContext):
        answer = update.message.text
        pattern = r'^(?P<hour>\d\d):(?P<minute>\d\d)(?P<timezone>[+-]\d)?$'
        match = re.fullmatch(pattern, answer)
        if not match:
            await edit_text(update, 'Invalid time: expected format HH:MM [+X|-X]')
            return 2

        data = match.groupdict()
        context.user_data.update(data)
        if context.user_data['timezone'] is None:
            context.user_data['timezone'] = '0'


    async def _process_result(self, update: Update, context: CallbackContext):
        chat_id = update.effective_chat.id

        sub_info = SubInfo(context.user_data['task'],
                           context.user_data['lang'],
                           int(context.user_data['hour']),
                           int(context.user_data['minute']),
                           int(context.user_data['timezone']))

        self.storage.add_sub(chat_id, sub_info)
        sub_message = ('✅ *Subscribed!*'
                      f'{JOB_NAMES[sub_info.task]} - {sub_info.hour}:{sub_info.minute:02d} GMT{sub_info.timezone:+}\n'
        )

        await edit_text(update, sub_message, parse_mode=ParseMode.MARKDOWN)
