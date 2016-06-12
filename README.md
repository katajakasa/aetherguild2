# aetherguild2

Website project for https://aetherguild.net

## 1. Installation

1. Copy aetherguild/config.py-dist to aetherguild/config.py
2. Edit the newly created aetherguild/config.py. Make sure you have AMQP vhost & mysql database set up.
3. pip install --upgrade -r requirements.txt
4. alembic upgrade head
5. Start by running `python -m aetherguild.listener_service.main` and `python -m aetherguild.socket_service.main`.

## 2. License

MIT. Please see LICENSE for details.