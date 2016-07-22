# aetherguild2

Website project for https://aetherguild.net

## 1. Installation

1. Copy aetherguild/config.py-dist to aetherguild/config.py
2. Edit the newly created aetherguild/config.py. Make sure you have RabbitMQ vhost & mysql database set up.
3. `pip install --upgrade -r requirements.txt`
4. `alembic upgrade head`
5. `npm install`
5. Start by running `python -m aetherguild.listener_service.main` and `python -m aetherguild.socket_service.main`.

## 2. Test data & management

It is possible to generate test data to the database automatically. Use command `python -m aetherguild.datagen`.

There are also tools for managing forums:
* `python -m aetherguild.manage_forum_boards` for board management
* `python -m aetherguild.manage_forum_sections` for section management
* `python -m aetherguild.manage_users` for user management

## 3. License

MIT. Please see LICENSE for details.