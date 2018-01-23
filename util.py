# -*- coding:utf-8 -*-
import subprocess
import re
import json
import os
import shutil
import random, string
import HTMLParser

#used by get_terminal_size
import fcntl, termios, struct
#used by Netease post request parameter encoding
from Crypto.Cipher import AES
import base64

def format_json(json_str):
    parsed = json.loads(json_str)
    return json.dumps(parsed, indent=4, sort_keys=True)

def get_terminal_size(fd=1):
    """
      Returns height and width of current terminal. First tries to get
      size via termios.TIOCGWINSZ, then from environment. Defaults to 25
      lines x 80 columns if both methods fail.

      :param fd: file descriptor (default: 1=stdout)

      from: http://blog.taz.net.au/2012/04/09/getting-the-terminal-size-in-python/
  """
    try:
        hw = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
    except Exception:
        try:
            hw = (os.environ['LINES'], os.environ['COLUMNS'])
        except Exception:
            hw = (25, 80)

    return hw

def random_str(length):
    return ''.join(random.choice(string.lowercase) for i in range(length))


def get_line(s):
    """get a gui line with given char"""
    return str(s)*72

def create_dir(dir_name):
    """create dir if doesn't exist"""
    if dir_name:
        if not os.path.isdir(dir_name):
            os.makedirs(dir_name)

def decode_html(s):
    try:
        return HTMLParser.HTMLParser().unescape(s)
    except Exception:
        return "Unknown"

def ljust(s,n,fillchar=' '):
    """ if string has unicode chars, the built-in l/rjust cannot 
    auto-adjust and align, that's why this two functions come"""
    no_ascii_list = re.findall(r'[^\x00-\x7F]+', s)
    ln = len(''.join(no_ascii_list))
    return s.ljust(n-ln, fillchar)


def rjust(s,n,fillchar=' '):
    no_ascii_list = re.findall(r'[^\x00-\x7F]+', s)
    ln = len(''.join(no_ascii_list))
    return s.rjust(n-ln, fillchar)

def rsa_encrypt(text, pubKey, modulus):
    text = text[::-1]
    rs = int(text.encode('hex'), 16) ** int(pubKey, 16) % int(modulus, 16)
    return format(rs, 'x').zfill(256)

def aes_encrypt(text, secKey):
    pad = 16 - len(text) % 16
    text = text + pad * chr(pad)
    encryptor = AES.new(secKey, 2, '0102030405060708')
    ciphertext = encryptor.encrypt(text)
    ciphertext = base64.b64encode(ciphertext)
    return ciphertext

