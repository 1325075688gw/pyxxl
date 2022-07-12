_engine = None


def get_engine():
    return _engine


def set_engine(engine):
    global _engine
    _engine = engine
