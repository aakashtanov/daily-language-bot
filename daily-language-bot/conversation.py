import logging
from typing import List, Tuple
from functools import wraps
from enum import Enum

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import (
    ConversationHandler, CommandHandler, CallbackQueryHandler,
    CallbackContext, MessageHandler, filters
)


logger = logging.getLogger(__name__)


class ActionButton:
    BACK = ('⬅️Back', 'action:back')
    CANCEL = ('❌Cancel', 'action:cancel')


def build_inline_keyboard(button_names: List[List[Tuple[str, str]]]) -> InlineKeyboardMarkup:
    buttons = []
    for line in button_names:
        line_buttons = [InlineKeyboardButton(name, callback_data=cd) for name, cd in line]
        buttons.append(line_buttons)
    return InlineKeyboardMarkup([[InlineKeyboardButton(name, callback_data=cd) for name, cd in line] for line in button_names])


def make_choice_keyboard(button_names: List[List[Tuple[str, str]]] = None, only_cancel: bool = False) -> InlineKeyboardMarkup:
    choice_kb = [[ActionButton.CANCEL] if only_cancel else [ActionButton.CANCEL, ActionButton.BACK]]
    return build_inline_keyboard(button_names + choice_kb) if button_names else build_inline_keyboard(choice_kb)


async def get_query(update: Update):
    query = update.callback_query
    await query.answer()
    return query, query.data.split(':')[1]


class StepTrigger(Enum):
    MESSAGE = 0,    # Callback is called for message typed in
    BUTTON = 1      # Callback is called for a button pressed


def conversation_step(step_no: int, trigger: StepTrigger = StepTrigger.MESSAGE, pattern: str = None):
    """
    Decorator for conversation steps.
    :param step_no: Step number
    :param trigger: What should trigger the step: message or a button
    :param pattern: If given, trigger the step with this pattern
    :return:
    """
    assert trigger == StepTrigger.MESSAGE and pattern is None or trigger == StepTrigger.BUTTON and pattern is not None
    def decorator(func):
        @wraps(func)
        async def wrapper(self, update: Update, context: CallbackContext, *args, **kwargs):
            res = await func(self, update, context, *args, **kwargs)
            if 'step_cache' not in context.user_data:
                context.user_data['step_cache'] = []
            context.user_data['step_cache'].append((step_no, update.effective_message.text, update.effective_message.reply_markup))
            if res is None: # default reaction to void return
            # Regular step finish
                if step_no == -1:
                    # Entry point finished
                    res = 0
                elif step_no + 1 == self.steps:
                    # Last step finished successfully
                    await self._process_result(update, context)
                    context.user_data.clear()
                    res = ConversationHandler.END
                else:
                    # Middle step finished
                    res = step_no + 1
            elif res == self.GO_TO_CONVERSATION_END: # early exit, defined by user -> process result
                await self._process_result(update, context)
                context.user_data.clear()
                res = ConversationHandler.END
            return res

        wrapper.step_number = step_no
        wrapper.type = trigger
        wrapper.pattern = pattern
        return wrapper

    return decorator


async def edit_text(update: Update, text: str, markup = None, parse_mode: ParseMode = None):
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode=parse_mode)
    elif update.message:
        await update.message.reply_text(text, reply_markup=markup, parse_mode=parse_mode)
    else:
        logger.error('Wrong update while editing text')


class BaseConversation(ConversationHandler):

    def __init__(self, name: str, timeout: int = None):
        super().__init__(entry_points=[CommandHandler(name, self.start)],
                         states={},
                         fallbacks=[CallbackQueryHandler(self.cancel), CommandHandler(name, self.restart)],
                         conversation_timeout=timeout,
                         allow_reentry=True)
        self.GO_TO_CONVERSATION_END = -1 # const to be returned to exit ahead of schedule
        self.__collect_steps_info()


    def __collect_steps_info(self):
        steps = []
        for attr_name in dir(self):
            try:
                attr = getattr(self, attr_name)
            except AttributeError:
                continue
            if callable(attr) and hasattr(attr, 'step_number'):
                steps.append(attr)
        for step in steps:
            handler = None
            if step.step_number not in self._states:
                self._states[step.step_number] = [CallbackQueryHandler(self.__process_action, pattern='^action:')]
                self.GO_TO_CONVERSATION_END += 1
            if step.type == StepTrigger.MESSAGE:
                handler = MessageHandler(filters.TEXT & ~filters.COMMAND, step)
            elif step.type == StepTrigger.BUTTON:
                handler = CallbackQueryHandler(step, pattern=step.pattern)
            self._states[step.step_number].append(handler)



    def _print_debug(self):
        print('\n'.join([f'{s}, {c}' for s, c in self._states.items()]))


    async def __process_action(self, update: Update, context: CallbackContext):
        query, answer = await get_query(update)
        if answer == 'cancel':
            return await self.cancel(update, context)
        if answer == 'back':
            # restore message
            step_no, text, markup = context.user_data['step_cache'].pop()
            await edit_text(update, text, markup)
            return step_no


    @property
    def steps(self):
        return len(self._states) - 1 # Do not count entry point


    async def cancel(self, update: Update, context: CallbackContext):
        context.user_data.clear()
        await edit_text(update, '❌Canceled', None)
        return ConversationHandler.END


    @conversation_step(-1)
    async def start(self, update: Update, context: CallbackContext):
        return 0


    async def restart(self, update: Update, context: CallbackContext):
        context.user_data.clear()
        return await self.start(update, context)


    async def _process_result(self, update: Update, result: CallbackContext):
        # Should be defined in derived class
        pass
