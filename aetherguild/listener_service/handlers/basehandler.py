# -*- coding: utf-8 -*-


def has_level(level):
    """ Checks if user has required userlevel
    :param level: Required userlevel
    """
    def _inner_has_privileges(method):
        def inner(instance, *args, **kwargs):
            if instance.session.has_level(level):
                method(instance, *args, **kwargs)
            else:
                instance.send_error(error_code=403, error_msg="Forbidden")
        return inner
    return _inner_has_privileges


def is_authenticated(method):
    """ Checks if user is authenticated
    """
    def inner(instance, *args, **kwargs):
        if instance.session.user is not None:
            method(instance, *args, **kwargs)
        else:
            instance.send_error(error_code=403, error_msg="Forbidden")
    return inner


class BaseHandler(object):
    def __init__(self, db_session, mq_session, user_session, connection_id, receipt_id, full_route):
        self.db = db_session
        self.mq = mq_session
        self.connection_id = connection_id
        self.session = user_session
        self.receipt_id = receipt_id
        self.full_route = full_route

    def handle(self, track_route, message):
        """
        Handler for incoming messages. This should be overwritten in handlers.
        :param track_route: Routing information.
        :param message: Incoming message packet in full
        """
        pass

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

    def send_error(self, error_code, error_msg):
        """ Helper for sending standard error packet to the web client
        :param error_code: Error code
        :param error_msg: Error message
        """
        self.send({
            'error': True,
            'payload': {
                'error_msg': error_msg,
                'error_code': error_code,
            }
        })

    def send_message(self, payload):
        """ Helper for sending a standard message packet to the web client
        :param payload: Message contents
        """
        self.send({
            'error': False,
            'payload': payload
        })

    def send_control(self, payload):
        """ Sens a control message to socket server
        :param payload: Message contents
        """
        self.send(payload, is_control=True)

