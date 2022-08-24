import user_agents


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    if not ip or ip == "unknown":
        ip = request.META.get("HTTP_X_REAL_IP").split(",")[0]
    return ip


def get_request_user_agent(request):
    return request.META.get("HTTP_USER_AGENT", "")


def shorten_user_agent(ua_str):
    user_agent = user_agents.parse(ua_str)
    if user_agent.device.family == "iOS-Device":
        device = "iPhone"
    else:
        device = user_agent.device.family
    return device + "| " + user_agent.os.family + " " + user_agent.os.version_string
