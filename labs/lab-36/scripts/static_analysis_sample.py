def build_message(name):
    if name is None:
        return "Unknown"
    return "Service: " + name


print(build_message("notification"))
