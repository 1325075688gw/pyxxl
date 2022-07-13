from peach.misc import local_zh_hans

_trans_default = {}


def set_local_language(language=None):
    global _trans_default
    if language == "en":
        _trans_default = {}
    else:
        _trans_default = local_zh_hans.trans_map


def get_text(message):
    global _trans_default
    return _trans_default.get(message, message)
