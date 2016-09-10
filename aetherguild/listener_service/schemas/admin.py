# -*- coding: utf-8 -*-

get_users_request = {
    'include_deleted': {
        'type': 'boolean',
        'required': True,
    },
    'start': {
        'type': 'integer',
        'required': False
    },
    'count': {
        'type': 'integer',
        'required': False
    }
}

delete_user_request = {
    'user': {
        'type': 'integer',
        'required': True
    }
}