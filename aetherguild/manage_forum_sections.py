# -*- coding: utf-8 -*-

import argparse

from listener_service.tables import ForumSection
import config

import tabulate
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


def add_section(a):
    if not a.title or len(a.title) > 64 or len(a.title) < 4:
        print("Section title must be between 4 and 32 characters long")
        return 1

    s = db_session()
    section = ForumSection()
    section.title = a.title
    section.sort_index = a.sortindex
    s.add(section)
    s.commit()
    s.close()

    print("Section {} succesfully added!".format(a.title))
    return 0


def del_section(a):
    if not a.id:
        print("ID parameter required")
        return 1

    s = db_session()
    ForumSection.delete(s, id=a.id)
    s.commit()
    s.close()

    print("Section {} deleted".format(a.id))
    return 0


def list_sections(a):
    s = db_session()
    sections = []
    for user in ForumSection.get_many(s):
        ser = user.serialize()
        sections.append(ser)
    s.close()
    headers = {
        'id': 'ID',
        'title': 'Title',
        'sort_index': 'Sort Index',
    }
    print(tabulate.tabulate(sections, headers, tablefmt="grid"))
    return 0


if __name__ == '__main__':
    ops_choices = ['add', 'delete', 'list']

    # Form the argument parser (first argument is positional and required)
    parser = argparse.ArgumentParser(description='Manage forum sections for the website')
    parser.add_argument('operation', nargs='+', choices=ops_choices, help='Operation')
    parser.add_argument('--id', type=int, help='Section ID', default=None)
    parser.add_argument('--title', type=str, help='Title')
    parser.add_argument('--sortindex', type=int, help='Sort index', default=0)
    args = parser.parse_args()

    # Initialize a database session
    db_session = sessionmaker()
    engine = create_engine(config.DATABASE_CONFIG, pool_recycle=3600)
    db_session.configure(bind=engine)

    # Find the correct operation function and call it with arguments as a parameter
    op = {
        'add': add_section,
        'delete': del_section,
        'list': list_sections
    }[args.operation[0]]
    exit(op(args))
