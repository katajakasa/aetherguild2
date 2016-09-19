# -*- coding: utf-8 -*-

get_news_posts = {
    'start': {
        'type': 'integer',
        'required': False,
        'min': 0
    },
    'count': {
        'type': 'integer',
        'required': False,
        'min': 0
    }
}

get_news_post = {
    'post': {
        'type': 'integer',
        'required': True
    }
}

insert_news_posts_request = {
    'message': {
        'type': 'string',
        'required': True
    },
    'header': {
        'type': 'string',
        'required': True
    }
}

delete_news_post_request = {
    'post': {
        'type': 'integer',
        'required': True
    }
}

update_news_post_request = {
    'post': {
        'type': 'integer',
        'required': True
    },
    'message': {
        'type': 'string',
        'required': True
    },
    'header': {
        'type': 'string',
        'required': True
    }
}
