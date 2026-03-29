# utils/user_context.py

_current_user_id = None

def get_current_user_id():
    """Retrieve the ID of the currently logged-in admin user."""
    return _current_user_id

def set_current_user_id(user_id):
    """Store the ID of the currently logged-in admin user."""
    global _current_user_id
    _current_user_id = user_id
