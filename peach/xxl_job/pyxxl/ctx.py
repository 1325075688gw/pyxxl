from typing import Any, Optional
import time

from peach.xxl_job.pyxxl.schema import RunData


_global_vars = {}


class GlobalVars:
    @staticmethod
    def _set_var(name: str, obj: Any) -> None:
        _global_vars[name] = obj

    @staticmethod
    def _get_var(name: str) -> Any:
        return _global_vars.get(name, {})

    @staticmethod
    def _delete_var(name: str):
        _global_vars.pop(name)

    @staticmethod
    def try_get(name: str) -> Optional[Any]:
        return _global_vars.get(name)

    @staticmethod
    def set_xxl_run_data(trace_id, data, append=False) -> None:
        if append:
            handle_log = data["handle_log"]
            time_stamp = handle_log.created  # 以2020/10/5 10:12:56为例子
            time_tuple = time.localtime(time_stamp)
            data_time = time.strftime("%Y-%m-%d %H:%M:%S", time_tuple)
            level_name = f'<span style="color: red;">{str(handle_log.levelname)}</span>'
            path_name = str(handle_log.pathname)
            func_name = f'<span style="color: red;">{str(handle_log.funcName)}</span>'
            lineno = f'<span style="color: red;">{str(handle_log.lineno)}</span>'
            path = path_name + ", in " + func_name + ", line " + lineno
            handle_log = f"\n{level_name} {data_time} {path}\n    {handle_log.msg}"  # type: ignore
            old_handle_log = GlobalVars.get_xxl_run_data(trace_id).get("handle_log", "")
            new_handle_log = old_handle_log + handle_log
            data = {"handle_log": new_handle_log}
        raw_data = GlobalVars.get_xxl_run_data(trace_id)
        raw_data.update(data)
        GlobalVars._set_var(trace_id, raw_data)

    @staticmethod
    def get_xxl_run_data(trace_id):
        return GlobalVars._get_var(trace_id)

    @staticmethod
    def delete_xxl_run_data(trace_id) -> RunData:
        return GlobalVars._delete_var(trace_id)


g = GlobalVars
