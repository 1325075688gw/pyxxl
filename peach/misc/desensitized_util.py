class LogFormat:
    @classmethod
    def _phone_format(cls, phone):
        if len(phone) >= 4:
            return phone[:3] + "****" + phone[-4:]
        else:
            return phone

    @classmethod
    def phone_format(cls, phone):
        if isinstance(phone, str):
            return cls._phone_format(phone)
        if isinstance(phone, list):
            result = []
            for v in phone:
                result.append(cls._phone_format(v))
            return result


def phone_format(phone):
    return LogFormat.phone_format(phone)
