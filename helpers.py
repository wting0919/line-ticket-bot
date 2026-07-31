import config


def get_state(user_id):
    return config.user_state.get(user_id)


def has_show_list(user_id):
    state = get_state(user_id)
    return bool(state and "shows" in state)


def get_current_shows(user_id):
    state = get_state(user_id)

    if not state:
        return None

    return state.get("shows")


def get_current_index(user_id):
    state = get_state(user_id)

    if not state:
        return None

    return state.get("current_index")


def set_current_index(user_id, index):
    state = get_state(user_id)

    if state:
        state["current_index"] = index


def set_show_list(user_id, mode, shows):
    config.user_state[user_id] = {
        "mode": mode,
        "shows": shows,
        "current_index": None,
    }


def clear_state(user_id):
    config.user_state.pop(user_id, None)