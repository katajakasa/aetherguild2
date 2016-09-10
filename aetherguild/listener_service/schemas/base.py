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