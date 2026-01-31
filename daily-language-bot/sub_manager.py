import json
import pathlib
import logging
from dataclasses import dataclass, asdict
from datetime import time, timezone, timedelta

from telegram.ext import CallbackContext

from .jobs import *

logger = logging.getLogger(__name__)


@dataclass
class SubInfo:
    task: str
    lang: str
    hour: int
    minute: int
    timezone: int # in format +2/-3


class SubManager:

    JOBS = {
        JobTypes.NUMBERS: send_daily_numbers,
        JobTypes.VERBS: send_daily_verbs
    }

    def __init__(self, data_dir: pathlib.Path, context: CallbackContext):
        self.data_dir = data_dir
        self.storage_path = data_dir / 'subs.json'
        self.data: dict[int, list[SubInfo]] = {}
        self.ctx = context
        self._load()
        self._restore_subs()


    def _restore_subs(self):
        for chat_id, subs in self.data.items():
            for sub_info in subs:
                logger.info(f'Restoring subscription for {chat_id} to {sub_info.task} at {sub_info.hour}:{sub_info.minute:02d} GMT{sub_info.timezone:+}')
                self._schedule_daily_job(chat_id, sub_info)

    def _load(self):
        if not self.storage_path.exists():
            logger.info(f'Creating new storage at {self.storage_path}')
            self._save()
            return {}

        with open(self.storage_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            for chat_id, subs in raw_data.items():
                self.data[int(chat_id)] = []
                for sub_info in subs:
                    self.data[int(chat_id)].append(SubInfo(*sub_info.values()))
            logger.debug(f'Loaded storage {self.data}')


    def _save(self):
        raw_data = {}
        for chat_id, subs in self.data.items():
            raw_data[str(chat_id)] = []
            for sub_info in subs:
                raw_data[str(chat_id)].append(asdict(sub_info))
        tmp = self.storage_path.with_suffix('.tmp')
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(raw_data, f, indent=4)
        tmp.replace(self.storage_path)


    def add_sub(self, chat_id: int, info: SubInfo):
        self._load()
        if chat_id not in self.data:
            self.data[chat_id] = [info]
        else:
            self.data[chat_id].append(info)
        self._save()
        self._schedule_daily_job(chat_id, info)



    def _schedule_daily_job(self, chat_id: int, info: SubInfo):
        logger.info(f'Scheduling job {info.task} for chat {chat_id} at {info.hour}:{info.minute:02d} GMT{info.timezone:+}')
        self.ctx.job_queue.run_daily(
            self.JOBS[JobTypes(info.task)],
            time=time(hour=info.hour, minute=info.minute, tzinfo=timezone(timedelta(hours=info.timezone))),
            name=f'{info.task}_{info.lang}_{chat_id}',
            chat_id=chat_id,
            data={'chat_id': chat_id, 'data_dir': self.data_dir, 'language': info.lang },
        )

    def remove_subs(self, chat_id: int):
        self._load()
        subs = self.data.pop(chat_id)
        for sub_info in subs:
            for job in self.ctx.job_queue.get_jobs_by_name(f'{sub_info.task}_{sub_info.lang}_{chat_id}'):
                job.schedule_removal()
        self._save()


    def remove_sub(self, chat_id: int, task: str) -> SubInfo:
        self._load()
        subs = self.data[chat_id]
        save = None
        for i, sub in enumerate(subs):
            if sub.task == task:
                save = subs.pop(i)
                break
        self._save()
        for job in self.ctx.job_queue.get_jobs_by_name(f'{save.task}_{save.lang}_{chat_id}'):
            job.schedule_removal()
        return save


    def has_sub(self, chat_id: int, task: str, lang: str) -> bool:
        self._load()
        if chat_id not in self.data:
            return False
        subs = self.data[chat_id]
        for sub in subs:
            if sub.task == task and sub.lang == lang:
                return True

        return False


    def get_subs(self, chat_id: int) -> list[SubInfo]:
        self._load()
        if len(self.data) == 0 or chat_id not in self.data:
            return []
        return self.data[chat_id]


    @property
    def subs(self) -> dict[int, list[SubInfo]]:
        self._load()
        return self.data
