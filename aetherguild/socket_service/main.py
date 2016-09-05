# -*- coding: utf-8 -*-

import logging
import sys
import signal

from tornado import web, ioloop

from aetherguild import config
from wshandler import WsHandler
from mq import MQConnection


if __name__ == '__main__':
    # Find correct log level
    level = {
        0: logging.DEBUG,
        1: logging.INFO,
        2: logging.WARNING,
        3: logging.ERROR,
        4: logging.CRITICAL
    }[config.LOG_LEVEL]

    # Set up the global log
    log_format = '[%(asctime)s] %(message)s'
    log_datefmt = '%d.%m.%Y %I:%M:%S'
    logging.basicConfig(stream=sys.stderr,
                        level=level,
                        format=log_format,
                        datefmt=log_datefmt)
    log = logging.getLogger(__name__)
    log.info("Opening server on %s:%d", config.ADDRESS, config.PORT)

    # Get our ioloop instance
    loop = ioloop.IOLoop.instance()

    # Open up MQ queue connection
    mq = MQConnection(io_loop=loop)
    mq.connect()

    # Set up websocket handler, and set it as a message handler for MQ messages
    ws = WsHandler
    ws.mq = mq
    mq.set_msg_handler(ws.on_queue_message)

    # Index and static handlers
    handlers = [
        (r'/ws', ws),
    ]
    conf = {
        'debug': config.DEBUG,
    }

    def sig_handler(signal, frame):
        mq.close()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    # Start up everything
    app = web.Application(handlers, **conf)
    app.listen(port=config.PORT, address=config.ADDRESS)
    loop.start()
    log.info("Shutting down")
