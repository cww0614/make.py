def escape_format_str(text):
    return text.replace("{", "{{").replace("}", "}}")


def to_list(thing):
    if not isinstance(thing, list):
        if isinstance(thing, str) or not hasattr(thing, "__iter__"):
            thing = [thing]

    return thing
