def classify_error(exc: Exception) -> str:
    text=f"{type(exc).__name__} {exc}".lower()
    if "timeout" in text: return "TIMEOUT"
    if any(x in text for x in ("auth","permission denied","unauthorized","401","logon failure","authentication")): return "AUTH_FAILED"
    if any(x in text for x in ("unreachable","refused","name or service","nodename","connection")): return "UNREACHABLE"
    return "FAILED"
