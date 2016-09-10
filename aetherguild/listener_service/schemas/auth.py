# -*- coding: utf-8 -*-


login_request = {
    'username': {
        'type': 'string',
        'required': True
    },
    'password': {
        'type': 'string',
        'required': True
    }
}


register_request = {
    'username': {
        'type': 'string',
        'required': True
    },
    'password': {
        'type': 'string',
        'required': True
    },
    'nickname': {
        'type': 'string',
        'required': True
    }
}

update_profile_request = {
    'old_password': {
        'type': 'string',
        'required': False
    },
    'new_password': {
        'type': 'string',
        'dependencies': ['old_password'],
        'required': False
    },
    'nickname': {
        'type': 'string',
        'required': True
    }
}

authenticate_request = {
    'session_key': {
        'type': 'string',
        'required': True
    }
}

set_avatar_request = {
    'url': {
        'type': 'string',
        'required': True
    }
}
