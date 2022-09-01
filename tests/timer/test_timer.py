import time
import pytest

from peach.timer.models import Task
from peach.timer.api import TaskHandler, add_task, register_handler


class TestHandler(TaskHandler):
    def handle(self, task):
        assert task.biz_code == "test"
        # assert task.biz_num == "001"
        print("===========", task.biz_num)
        time.sleep(1)

    def get_biz_code(self):
        return "test"


@pytest.fixture
def task_data():
    add_task("test", "001")
    register_handler(TestHandler())


@pytest.mark.django_db(transaction=True)
def test_timer(task_data):
    assert Task.objects.filter(biz_code="test", biz_num="001").first().biz_num == "001"

    # start()
