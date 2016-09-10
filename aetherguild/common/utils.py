# -*- coding: utf-8 -*-

import os
import binascii


def generate_random_key():
    return binascii.hexlify(os.urandom(16))
