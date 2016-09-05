# -*- coding: utf-8 -*-


base_request = {
    'route': {
        'type': 'string',
        'required': True
    },
    'receipt': {
        'type': ['string', 'integer'],
        'required': False
    },
    'data': {
        'type': 'dict',
        'required': True,
        'allow_unknown': True,
        'schema': {}
    }
}


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

profile_request = {
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
        'required': False
    }
}

authenticate_request = {
    'session_key': {
        'type': 'string',
        'required': True
    }
}

get_boards_request = {
    'section': {
        'type': 'integer'
    }
}

get_threads_request = {
    'start': {
        'type': 'integer',
        'required': False
    },
    'count': {
        'type': 'integer',
        'required': False
    },
    'board': {
        'type': 'integer',
        'required': True
    },
}

get_posts_request = {
    'start': {
        'type': 'integer',
        'required': False
    },
    'count': {
        'type': 'integer',
        'required': False
    },
    'thread': {
        'type': 'integer',
        'required': True
    },
}

get_post_request = {
    'post': {
        'type': 'integer',
        'required': True
    },
}

insert_post_request = {
    'thread': {
        'required': True,
        'type': 'integer'
    },
    'message': {
        'required': True,
        'type': 'string'
    }
}

update_post_request = {
    'post': {
        'required': True,
        'type': 'integer'
    },
    'message': {
        'required': True,
        'type': 'string'
    },
    'edit_message': {
        'required': False,
        'type': 'string'
    },
}

insert_thread_request = {
    'board': {
        'required': True,
        'type': 'integer'
    },
    'title': {
        'required': True,
        'type': 'string'
    },
    'message': {
        'required': True,
        'type': 'string'
    },
    'closed': {
        'required': True,
        'type': 'boolean'
    },
    'sticky': {
        'required': True,
        'type': 'boolean'
    },
}

update_thread_request = {
    'thread': {
        'required': True,
        'type': 'integer'
    },
    'board': {
        'required': False,
        'type': 'integer'
    },
    'title': {
        'required': False,
        'type': 'string'
    },
    'closed': {
        'required': False,
        'type': 'boolean'
    },
    'sticky': {
        'required': False,
        'type': 'boolean'
    },
}