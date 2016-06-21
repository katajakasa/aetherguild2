# -*- coding: utf-8 -*-

import argparse
import config
import sys
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from tests.helper import DatabaseTestHelper


if __name__ == '__main__':
    # Form the argument parser (first argument is positional and required)
    parser = argparse.ArgumentParser(description=u'Add test data to database (Avoid running in production)')
    parser.add_argument('--i_know_the_risks', type=bool, help='Set to True if you are sure', default=False)
    args = parser.parse_args()

    if not args.i_know_the_risks:
        sys.exit(0)

    helper = DatabaseTestHelper()
    helper.engine = create_engine(config.DATABASE_CONFIG, pool_recycle=3600)
    helper.db = sessionmaker(bind=helper.engine)

    helper.create_test_users()
    helper.create_test_forum()

    print("Test data added.")
    sys.exit(0)
