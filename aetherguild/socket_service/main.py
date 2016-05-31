# -*- coding: utf-8 -*-

from aetherguild import config
import logging
from tornado import web, ioloop


if __name__ == '__main__':
    log = logging.getLogger(__name__)

    # Index and static handlers
    handlers = [
        (r'/(.*)$', web.StaticFileHandler, {'path': config.PUBLIC_PATH, 'default_filename': 'index.html'}),
    ]
    conf = {
        'debug': config.DEBUG,
    }

    # Start up everything
    app = web.Application(handlers, **conf)
    app.listen(config.PORT)
    loop = ioloop.IOLoop.instance()
    try:
        loop.start()
    except KeyboardInterrupt:
        loop.stop()
