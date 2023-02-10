import atexit

from multiprocessing.util import _exit_function  # type: ignore

from peach.xxl_job.pyxxl import ExecutorConfig, PyxxlRunner


bind = ["0.0.0.0:8000"]
backlog = 512
workers = 1
timeout = 300
graceful_timeout = 2
limit_request_field_size = 8192


def when_ready(server):
    # pylint: disable=import-outside-toplevel,unused-import,no-name-in-module
    from app import xxl_handler

    atexit.unregister(_exit_function)

    config = ExecutorConfig(
        xxl_admin_k8s_baseurl="http://localhost:8080/xxl-job-admin/api/",
        executor_app_name="xxl_job-sample",
        executor_host="172.17.0.1",
    )

    runner = PyxxlRunner(config, handler=xxl_handler)
    server.pyxxl_runner = runner
    runner.run_with_daemon()
