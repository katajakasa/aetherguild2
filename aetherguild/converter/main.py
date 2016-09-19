# -*- coding: utf-8 -*-

import sys

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from aetherguild.converter import old_tables
from aetherguild.listener_service import tables as new_tables

import binascii


level_conv_table = {
    0: 0,  # guest to guest
    1: 0,  # newbie to guest
    2: 1,  # user to user
    3: 2,  # admin to admin
    4: 2   # root to admin
}

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Target database required as the first argument, source database as second!")
        exit(1)

    # Connect to destination database
    #dst_engine_str = "postgresql+psycopg2://{}".format(sys.argv[1])
    dst_engine_str = "mysql+pymysql://{}?charset=utf8mb4".format(sys.argv[1])
    dst_engine = create_engine(dst_engine_str, pool_recycle=3600)
    dst_connection = sessionmaker(bind=dst_engine)

    # Connect to source database
    src_engine_str = "mysql+pymysql://{}?charset=utf8mb4".format(sys.argv[2])
    src_engine = create_engine(src_engine_str, pool_recycle=3600)
    src_connection = sessionmaker(bind=src_engine)

    # Create sessions
    dst_session = dst_connection()
    src_session = src_connection()

    # Old_user: New_user
    user_mapping = {}
    section_mapping = {}
    board_mapping = {}
    thread_mapping = {}

    # Clear new tables
    dst_session.query(new_tables.Session).delete()
    dst_session.query(new_tables.OldUser).delete()
    dst_session.query(new_tables.User).delete()
    dst_session.query(new_tables.ForumPostEdit).delete()
    dst_session.query(new_tables.ForumLastRead).delete()
    dst_session.query(new_tables.ForumPost).delete()
    dst_session.query(new_tables.ForumThread).delete()
    dst_session.query(new_tables.ForumBoard).delete()
    dst_session.query(new_tables.ForumSection).delete()

    # Transfer users
    for old_user in old_tables.User.get_many(src_session):
        old_pw = binascii.hexlify(old_user.password)
        if old_pw == '0000000000000000000000000000000000000000000000000000000000000000':
            old_pw = None

        new_user = new_tables.User()
        new_user.username = old_user.username
        new_user.nickname = old_user.alias
        new_user.deleted = not old_user.active or not old_pw or old_user.spambot
        new_user.created_at = old_user.registered
        new_user.last_contact = old_user.lastcontact
        new_user.level = level_conv_table[old_user.level]
        dst_session.add(new_user)
        dst_session.flush()

        # Old user table, fill in old password
        if old_user.active and old_pw and not old_user.spambot:
            new_user_pw = new_tables.OldUser()
            new_user_pw.password = old_user.password
            new_user_pw.user = new_user.id
            dst_session.add(new_user_pw)

        # Create mapping and print info
        user_mapping[old_user.id] = new_user.id
        print(u"[user   ] {} migrated".format(new_user.username))

    # Transfer sections
    for old_section in old_tables.ForumSection.get_many(src_session):
        new_section = new_tables.ForumSection()
        new_section.title = old_section.title
        new_section.sort_index = old_section.sort_index
        dst_session.add(new_section)
        dst_session.flush()
        section_mapping[old_section.id] = new_section.id
        print(u"[section] {} migrated".format(new_section.title))

    # Transfer boards
    for old_board in old_tables.ForumBoard.get_many(src_session):
        new_board = new_tables.ForumBoard()
        new_board.section = section_mapping[old_board.sid]
        new_board.title = old_board.title
        new_board.description = old_board.description
        new_board.sort_index = old_board.sort_index
        new_board.req_level = level_conv_table[old_board.min_read_level]
        dst_session.add(new_board)
        dst_session.flush()
        board_mapping[old_board.id] = new_board.id
        print(u"[board  ] {} migrated".format(new_board.title))

    # Transfer threads
    for old_thread in old_tables.ForumThread.get_many(src_session):
        new_thread = new_tables.ForumThread()
        new_thread.board = board_mapping[old_thread.bid]
        new_thread.user = user_mapping[old_thread.uid]
        new_thread.title = old_thread.title
        new_thread.created_at = old_thread.post_time
        new_thread.views = old_thread.views
        new_thread.sticky = old_thread.sticky
        new_thread.closed = old_thread.closed
        dst_session.add(new_thread)
        dst_session.flush()
        thread_mapping[old_thread.id] = new_thread.id
        print(u"[thread ] {} migrated".format(new_thread.title))

    # Transfer users, edits
    for old_post in old_tables.ForumPost.get_many(src_session):
        new_post = new_tables.ForumPost()
        new_post.user = user_mapping[old_post.uid]
        new_post.thread = thread_mapping[old_post.tid]
        new_post.created_at = old_post.post_time
        new_post.message = old_post.message
        dst_session.add(new_post)
        dst_session.flush()
        print(u"[post   ] {} migrated".format(new_post.id))

    # Transfer news items
    for old_news in old_tables.NewsModel.get_many(src_session):
        new_news = new_tables.NewsItem()
        new_news.nickname = "Akvavitix"
        new_news.header = old_news.header
        new_news.message = old_news.message
        new_news.created_at = old_news.time
        dst_session.add(new_news)
        dst_session.flush()
        print(u"[news   ] {} migrated".format(new_news.id))

    # Commit all changes
    dst_session.commit()
