def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    if not ip or ip == "unknown":
        ip = request.META.get("HTTP_X_REAL_IP").split(",")[0]
    return ip
