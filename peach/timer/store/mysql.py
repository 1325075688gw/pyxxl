import logging

from django.db.models import F
from peach.misc import dt

# 每次批量处理的任务数量
from peach.timer.models import Task

batch_undo_rows = 10
_LOGGER = logging.getLogger(__name__)


class MySqlTaskStore:
    def add_task(self, biz_code, biz_num, when, biz_ext=None):
        _task, created = Task.objects.update_or_create(
            biz_code=biz_code,
            biz_num=biz_num,
            defaults=dict(when=when, biz_ext=biz_ext),
        )
        return _task.id

    def finished_task(self, biz_code, biz_num):
        Task.objects.filter(biz_code=biz_code, biz_num=biz_num).delete()

    def get_undo_tasks(self, count=None):
        now = dt.local_now()
        undo_tasks = Task.objects.filter(status=0, when__lte=now).order_by("when")[
            : count or batch_undo_rows
        ]

        lock_tasks = []

        for task in undo_tasks:
            # 乐观锁
            rows = Task.objects.filter(
                id=task.id, status=0, version=task.version
            ).update(status=1, version=F("version") + 1, update_time=now)
            if rows == 1:
                lock_tasks.append(task)

        return lock_tasks

    def get_tasks_by_code(self, biz_code=None, biz_num=None, when=None):
        tasks = Task.objects.filter(status=0)
        if biz_code:
            tasks = tasks.filter(biz_code=biz_code)
        if biz_num:
            tasks = tasks.filter(biz_num__icontains=biz_num)
        if when:
            tasks = tasks.filter(when__gt=when)
        return tasks

    def retry_task(self, biz_code, biz_num, next_time=None):
        Task.objects.filter(biz_code=biz_code, biz_num=biz_num).update(
            when=next_time or dt.local_now(), status=0
        )

    def close(self):
        pass


def get_store():
    if "mysql" == "mysql":
        return MySqlTaskStore()
    else:
        raise NotImplementedError('you config "%s" store type not implemented')


store_engine = get_store()
