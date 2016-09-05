# -*- coding: utf-8 -*-

from passlib.hash import pbkdf2_sha512


def validate_str_length(field, value, error_list, min_value=None, max_value=None):
    if (min_value and len(value) < min_value) or (max_value and len(value) > max_value):
        if min_value and not max_value:
            error_list.add_error(u'Must be at least {} characters long'.format(min_value), field)
        if not min_value and max_value:
            error_list.add_error(u'Must be at maximum {} characters long'.format(max_value), field)
        if min_value and max_value:
            error_list.add_error(u'Must be between {} and {} characters long'.format(min_value, max_value), field)


def validate_required_field(field, value, error_list):
    if len(value) == 0:
        error_list.add_error(u'Required field', field)


def validate_password_field(field, old_password, test_password, error_list):
    if not pbkdf2_sha512.verify(test_password, old_password):
        error_list.add_error(u"Incorrect password", field)
