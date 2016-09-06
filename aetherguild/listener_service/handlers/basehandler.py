# -*- coding: utf-8 -*-

from cerberus import Validator


def has_level(level):
    """ Checks if user has required userlevel
    :param level: Required userlevel
    """
    def _inner_has_privileges(method):
        def inner(instance, *args, **kwargs):
            if instance.session.user is not None and instance.session.has_level(level):
                method(instance, *args, **kwargs)
            else:
                instance.send_error(403, u"Forbidden")
        return inner
    return _inner_has_privileges


def is_authenticated(method):
    """ Checks if user is authenticated
    """
    def inner(instance, *args, **kwargs):
        if instance.session.user is not None:
            method(instance, *args, **kwargs)
        else:
            instance.send_error(403, u"Forbidden")
    return inner


def validate_message_schema(schema):
    """ Validates function input message against a schema, and returns error 400 if the check fails
    """
    def _inner_has_privileges(method):
        def inner(instance, *args, **kwargs):
            v = Validator(schema)
            if v.validate(args[1].get('data')):
                method(instance, *args, **kwargs)
            else:
                errors_list = ErrorList()
                for err_field, err_messages in v.errors.items():
                    for err_message in err_messages:
                        errors_list.add_error(error_message=err_message, error_field=err_field)
                instance.send_error(400, errors_list)
        return inner
    return _inner_has_privileges


class ErrorList(object):
    def __init__(self, error_message=None, error_field=None):
        self.error_list = []
        if error_message:
            self.add_error(error_message, error_field)

    def add_error(self, error_message, error_field=None):
        if error_field:
            self.error_list.append({
                'field': error_field,
                'message': error_message
            })
        else:
            self.error_list.append({
                'message': error_message
            })

    def get_list(self):
        return self.error_list


class BaseHandler(object):
    def __init__(self, db_session, mq_session, user_session, connection_id, receipt_id, full_route):
        self.db = db_session
        self.mq = mq_session
        self.connection_id = connection_id
        self.session = user_session
        self.receipt_id = receipt_id
        self.full_route = full_route

    def get_routes(self):
        """
        Should be overwritten to return a route description dict
        :return: Route dict
        """
        return {}

    def handle(self, track_route, message):
        cb = self.get_routes().copy()
        try:
            while type(cb) == dict:
                cb = cb[track_route.pop(0)]
            cb(track_route, message)
        except IndexError:
            self.send_error(404, u'Route not found')

    def send(self, message, is_control=False):
        assert type(message) == dict, "Message type must be dict"
        message.setdefault('route', self.full_route)
        if self.receipt_id and not is_control:
            message['receipt'] = self.receipt_id
        self.mq.publish(
            message=message,
            connection_id=self.connection_id,
            is_control=is_control)

    def broadcast(self, message, is_control=False, avoid_self=False, req_level=0):
        assert type(message) == dict, "Message type must be dict"
        message.setdefault('route', self.full_route)
        self.mq.publish(
            message=message,
            connection_id=self.connection_id,
            broadcast=True,
            is_control=is_control,
            avoid_self=avoid_self,
            req_level=req_level)

    def send_error(self, error_code, error_msgs):
        """ Helper for sending standard error packet to the web client
        :param error_code: Error code
        :param error_msg: Error messages list. Str, Unicode, ErrorList objects are valid.
        """
        assert type(error_code) == int, "Error code must be integer"
        assert type(error_msgs) in (unicode, str, ErrorList), "Error messages must be unicode, str or ErrorList object"

        error_list = error_msgs
        if type(error_list) == str or type(error_list) == unicode:
            error_list = ErrorList(error_list)

        self.send({
            'error': True,
            'data': {
                'error_messages': error_list.get_list(),
                'error_code': error_code,
            }
        })

    def send_message(self, data):
        """ Helper for sending a standard message packet to the web client
        :param data: Message contents
        """
        self.send({
            'error': False,
            'data': data
        })

    def send_control(self, data):
        """ Sens a control message to socket server
        :param data: Message contents
        """
        self.send(data, is_control=True)

    def broadcast_message(self, data, avoid_self=False, req_level=0):
        """ Helper for sending a standard message packet to the web client
        :param data: Message contents
        :param avoid_self: Avoid self when broadcasting message
        :param req_level: Required client userlevel to receive this broadcast
        """
        self.broadcast({
            'error': False,
            'data': data
        }, avoid_self=avoid_self, req_level=req_level)
