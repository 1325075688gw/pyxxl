from typing import Any, Optional
import time

from peach.xxl_job.pyxxl.schema import RunData
from peach.helper.global_var.global_var import GlobalVar

from contextvars import ContextVar


ColorDict = {
    "DEBUG": "black",
    "INFO": "green",
    "WARNING": "blue",
    "WARN": "blue",
    "EXCEPTION": "red",
    "ERROR": "red",
}


class GlobalVars:
    @staticmethod
    def _set_var(name: str, obj: Any) -> None:
        GlobalVar.global_dict[name] = obj

    @staticmethod
    def _get_var(name: str) -> Any:
        return GlobalVar.global_dict.get(name, {})

    @staticmethod
    def _delete_var(name: str):
        GlobalVar.global_dict.pop(name, None)

    @staticmethod
    def try_get(name: str) -> Optional[Any]:
        return GlobalVar.global_dict.get(name)

    @staticmethod
    def set_xxl_run_data(trace_id, data, append=False) -> None:
        if append:
            handle_log = data["handle_log"]
            time_stamp = handle_log.created  # 以2020/10/5 10:12:56为例子
            time_tuple = time.localtime(time_stamp)
            data_time = (
                f'<span style="color: {ColorDict.get(str(handle_log.levelname).upper(), "black")};">'
                f'{time.strftime("%Y-%m-%d %H:%M:%S", time_tuple)}</span>'
            )
            level_name = f'<span style="color: {ColorDict.get(str(handle_log.levelname).upper(), "black")};">{str(handle_log.levelname)}</span>'
            path_name = f'<span style="color: {ColorDict.get(str(handle_log.levelname).upper(), "black")};">{str(handle_log.name)}</span>'
            func_name = f'<span style="color: {ColorDict.get(str(handle_log.levelname).upper(), "black")};">{str(handle_log.funcName)}</span>'
            lineno = f'<span style="color: {ColorDict.get(str(handle_log.levelname).upper(), "black")};">{str(handle_log.lineno)}</span>'
            xxl_kwargs = g2.xxl_run_data
            log_id = xxl_kwargs.get("run_data", {}).get("logId", "")
            path = (
                path_name
                + ", in "
                + func_name
                + ", line "
                + lineno
                + ", logId="
                + str(log_id)
            )
            handle_log = f"\n{level_name} {data_time} {path}\n     {handle_log.msg}"  # type: ignore
            old_handle_log = GlobalVars.get_xxl_run_data(trace_id).get("handle_log", "")
            new_handle_log = old_handle_log + handle_log
            data = {"handle_log": new_handle_log}
        raw_data = GlobalVars.get_xxl_run_data(trace_id)
        raw_data.update(data)
        GlobalVars._set_var(trace_id, raw_data)
        xxl_kwargs = g2.xxl_run_data
        log_id = xxl_kwargs.get("run_data", {}).get("logId", "")
        if log_id:
            GlobalVars._set_var(log_id, raw_data)

    @staticmethod
    def get_xxl_run_data(trace_id):
        return GlobalVars._get_var(trace_id)

    @staticmethod
    def get_xxl_run_data_log_id(log_id):
        return GlobalVars._get_var(log_id)

    @staticmethod
    def delete_xxl_run_data(trace_id) -> RunData:
        return GlobalVars._delete_var(trace_id)


g = GlobalVars


_global_vars: ContextVar[dict] = ContextVar("pyxxl_vars", default={})


class GlobalVars2:
    @staticmethod
    def _set_var(name: str, obj: Any) -> None:
        _global_vars.get()[name] = obj

    @staticmethod
    def _get_var(name: str) -> Any:
        try:
            return _global_vars.get()[name]
        except Exception:
            return {}

    @staticmethod
    def try_get(name: str) -> Optional[Any]:
        return _global_vars.get().get(name)

    @staticmethod
    def set_xxl_run_data(data) -> None:
        GlobalVars2._set_var("xxl_kwargs", data)

    @property
    def xxl_run_data(self):
        return self._get_var("xxl_kwargs")


g2 = GlobalVars2()
