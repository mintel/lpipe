sentinel = object()


def get_nested(_dict, keys, default=sentinel):
    """Given a dictionary or object, try to fetch a key nested several levels deep."""

    def _get(head, k, d):
        if isinstance(head, dict):
            return head.get(k, d)
        else:
            return getattr(head, k, d)

    head = _dict
    for k in keys:
        head = _get(head, k, default)
        if head is sentinel:
            raise KeyError(f"{keys}")
        elif not head:
            return head
    return head


def set_nested(d, keys, value):
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value
