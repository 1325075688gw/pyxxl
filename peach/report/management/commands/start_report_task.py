# -*- coding: utf-8 -*-
import signal
from django.core.management.base import BaseCommand

from peach.report.executor import stop, run


def kill_report_task_when_signal(signum, frame):
    stop()


class Command(BaseCommand):
    help = "Start task command."

    def handle(self, *args, **options):
        run()
        signal.signal(signal.SIGINT, kill_report_task_when_signal)
        signal.signal(signal.SIGTERM, kill_report_task_when_signal)
        self.stdout.write("report dog 启动成功......")
