from core.cc1101.ccrf import pCC1101

_instance = None


def get_instance():
    global _instance
    if _instance is None:
        try:
            _instance = pCC1101()
        except Exception:
            raise
            _instance = False
    return _instance


def shutdown():
    global _instance
    if _instance is not None:
        try:
            _instance.close()
        except Exception:
            pass
        _instance = None
