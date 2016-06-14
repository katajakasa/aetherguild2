# -*- coding: utf-8 -*-

import argparse

from listener_service.tables import ForumBoard, ForumSection
import config

import tabulate
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import create_engine


def add_board(a):
    if not a.title or len(a.title) > 64 or len(a.title) < 4:
        print("Board title must be between 4 and 32 characters long")
        return 1

    if not a.description or len(a.description) < 4:
        print("Board description must be at least 4 characters long.")
        return 1

    s = db_session()

    try:
        section = ForumSection.get_one(s, id=a.section)
    except NoResultFound:
        print("Section {} does not exist.".format(a.section))
        return 1

    board = ForumBoard()
    board.title = a.title
    board.section = section.id
    board.description = a.description
    board.min_write_level = a.min_write_level
    board.min_read_level = a.min_read_level
    board.sort_index = a.sortindex
    s.add(board)
    s.commit()
    s.close()

    print("Board {} succesfully added!".format(a.title))
    return 0


def del_board(a):
    if not a.id:
        print("ID parameter required")
        return 1

    s = db_session()
    ForumBoard.delete(s, id=a.id)
    s.commit()
    s.close()

    print("Board {} deleted".format(a.id))
    return 0


def list_boards(a):
    s = db_session()
    boards = []
    for board in ForumBoard.get_many(s):
        ser = board.serialize()
        section = ForumSection.get_one(s, id=ser['section'])
        ser['section'] = u'{} ({})'.format(section.title, section.id)
        boards.append(ser)
    s.close()
    headers = {
        'id': 'ID',
        'section': 'Section',
        'title': 'Title',
        'description': 'Description',
        'min_read_level': 'Min. R. level',
        'min_write_level': 'Min. W. level',
        'sort_index': 'Sort Index'
    }
    print(tabulate.tabulate(boards, headers, tablefmt="grid"))
    return 0


if __name__ == '__main__':
    ops_choices = ['add', 'delete', 'list']

    # Form the argument parser (first argument is positional and required)
    parser = argparse.ArgumentParser(description='Manage forum sections for the website')
    parser.add_argument('operation', nargs='+', choices=ops_choices, help='Operation')
    parser.add_argument('--id', type=int, help='Board ID', default=None)
    parser.add_argument('--title', type=str, help='Title')
    parser.add_argument('--description', type=str, help='Description')
    parser.add_argument('--section', type=int, help='Section ID')
    parser.add_argument('--min_read_level', type=int, help='Min Read Level')
    parser.add_argument('--min_write_level', type=int, help='Min Write Level')
    parser.add_argument('--sortindex', type=int, help='Sort index', default=0)
    args = parser.parse_args()

    # Initialize a database session
    db_session = sessionmaker()
    engine = create_engine(config.DATABASE_CONFIG, pool_recycle=3600)
    db_session.configure(bind=engine)

    # Find the correct operation function and call it with arguments as a parameter
    op = {
        'add': add_board,
        'delete': del_board,
        'list': list_boards
    }[args.operation[0]]
    exit(op(args))
