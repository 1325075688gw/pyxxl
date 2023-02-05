from typing import Any, Optional

from peach.xxl_job.pyxxl.schema import RunData


_global_vars = {}


class GlobalVars:
    @staticmethod
    def _set_var(name: str, obj: Any) -> None:
        _global_vars[name] = obj

    @staticmethod
    def _get_var(name: str) -> Any:
        return _global_vars.get(name)

    @staticmethod
    def _delete_var(name: str):
        _global_vars.pop(name)

    @staticmethod
    def try_get(name: str) -> Optional[Any]:
        return _global_vars.get(name)

    @staticmethod
    def set_xxl_run_data(data: RunData) -> None:
        GlobalVars._set_var(data.traceID, {"xxl_kwargs": data})

    @staticmethod
    def get_xxl_run_data(trace_id) -> RunData:
        return GlobalVars._get_var(trace_id).get("xxl_kwargs")

    @staticmethod
    def delete_xxl_run_data(trace_id) -> RunData:
        return GlobalVars._delete_var(trace_id)


g = GlobalVars
