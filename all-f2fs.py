#!/usr/bin/env python
# coding=utf-8

from __future__ import print_function
from os.path import abspath, dirname, exists, join
import re
from shutil import copyfile
from zipfile import ZipFile


__author__ = '1337@github.com'


def convert(original_path):
    """Given a ROM zip path, converts installer instructions to use
    F2Fs volumes.

    :param original_path: some string like '/opt/whatever.zip'
    :returns the path of the converted zip.
    """
    def repl(m):
        """Converts mount or formats to F2FS equivalents.
        :param m: regex match
        """
        news = ''
        if m.group(1) == 'mount':
            news = r'run_program("/sbin/busybox", "mount", "{}");'.format(
                m.group(4))
        if m.group(1) == 'format':
            news = r'run_program("/sbin/mkfs.f2fs", "{}");'.format(m.group(2))

        if not news:
            raise ValueError("unexpected directive '{}'".format(m.group(1)))

        return news

    updater_script_path = "META-INF/com/google/android/updater-script"

    print("Uncompressing '{}' ...".format(original_path))
    with ZipFile(original_path) as rom_file:
        updater_script = rom_file.read(updater_script_path)
    if not updater_script:
        raise ValueError("Could not read updater script in '{}'".format(
            original_path))

    # create new script contents
    updater_script = re.sub(
        r'^(mount|format)'  # 'mount' or 'format'
        r'\("ext4",\s*"EMMC",\s*'  # the "ext4", "EMMC"
        r'"([^"]+)",\s*'  # the '/dev/block/...'
        r'("\d"\s*,\s*)?'  # the "0" in format calls
        r'"([^"]+)"\);\s*$',  # the partition
        repl, updater_script, flags=re.MULTILINE)

    # create write target
    new_path = original_path.replace('.zip', '-f2fs.zip')
    if not '.zip' in new_path:
        new_path += '-f2fs.zip'

    print("Creating F2FS ROM {}...".format(new_path))
    copyfile(original_path, new_path)

    # pack replacement
    with ZipFile(new_path, 'a') as rom_file:
        rom_file.writestr(updater_script_path, updater_script)

    return new_path


if __name__ == '__main__':
    default_filename = join(abspath(dirname(__file__)), 'rom.zip')
    filename = raw_input('Enter location of your ROM ({}): '.format(
        default_filename)) or default_filename
    if not (filename and exists(abspath(filename))):
        print("Aborted: '{}' does not exist".format(abspath(filename)))
        exit(137)

    dest = convert(filename)  # if it fails, it'll tell you
    print("Updated ROM saved to: {}\n".format(dest))
    exit(0)