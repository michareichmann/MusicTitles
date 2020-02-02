#!/usr/bin/env python
# --------------------------------------------------------
#       small script to rename music titles
# created on March 4th 2017 by M. Reichmann (micha.reichmann@gmail.com)
# --------------------------------------------------------

from glob import glob
from mouse import Mouse
from keys import Keys
from argparse import ArgumentParser
from os.path import join, basename, dirname, realpath, isdir
from shutil import move
from re import split
from datetime import datetime
from tinytag import TinyTag
import eyed3
# from Utils import *


class Titles(Keys, Mouse):
    def __init__(self, file_dir):
        self.FileDir = file_dir
        self.Band = self.get_band()
        self.Album = self.get_album()
        self.ExcludeTypes = ['ini', 'jpg', 'txt']
        self.Exclude = [self.Band, self.Album, '(mp3co.biz)']
        self.Songs = self.load_songs()
        Keys.__init__(self)
        Mouse.__init__(self)

    def get_band(self):
        band = basename(dirname(realpath(self.FileDir)))
        return self.get_album() if band == 'Music' else band

    def get_album(self):
        return basename(realpath(self.FileDir))

    def load_songs(self):
        return [name for name in glob(join(self.FileDir, '*')) if not any(name.endswith('.{}'.format(typ)) for typ in self.ExcludeTypes)]

    def reload_songs(self):
        self.Songs = self.load_songs()

    def rename_albums(self):
        for name in glob(join(self.FileDir, '*')):
            data = [word.title() for word in basename(name).split()]
            if '-' not in data:
                new_name = ' '.join([' - '.join(data[:2])] + data[2:])
            else:
                new_name = ' '.join(data)
            move(name, new_name)

    def rename_album(self, name, exclude):
        exclude = [exclude, self.Band]
        old_name = name
        name = basename(name)
        for word in exclude:
            if len(name) > len(word) * 2:
                name = name.replace(word, '', 1)
        words = [word.title() for word in split('[ -]', name) if word]
        try:
            datetime.strptime(words[0], '%Y')
            name = ' '.join([' - '.join(words[:2])] + words[2:])
        except ValueError:
            for title in glob(join(old_name, '*')):
                try:
                    tag = TinyTag.get(title)
                    name = None
                    if tag.year is not None:
                        print tag.year, words
                        name = ' '.join([' - '.join([tag.year, words[0]])] + words[1:])
                        break
                except LookupError:
                    pass
        name = join(self.FileDir, name)
        if old_name != name:
            print '{0} -> {1}'.format(old_name, name)
            move(old_name, name)
        return name

    def rename_all(self, exclude=''):
        for name in glob(join(self.FileDir, '*')):
            album = self.rename_album(name, exclude)
            self.Album = basename(album).split(' - ')[-1]
            print self.Album
            for title in glob(join(album, '*')):
                self.rename_title(title, exclude)
            print '-' * 20

    def rename_title(self, name, excl_str, has_num=None):
        old_name = name
        if isdir(name):
            print name, 'is a dir'
            for title in glob(join(name, '*')):
                self.rename_title(title, excl_str)
            return
        name = basename(name).replace('.mp3', '').replace('.Mp3', '')
        for word in self.Exclude + [excl_str]:
            if len(name) > len(word) + 5:
                name = name.replace(word, '', 1)
        data = [word.strip(' _').title() for word in split('[ ._-]', name) if word]
        data = filter(lambda w: not (w.isdigit() and len(w) == 4), data)
        self.fix_bonus_track(data)
        start_index = data.index(next(word for word in data if word.isdigit())) + 1 if has_num else 0  # start from the index after the first number
        new_name = ' '.join(data[start_index:])
        new_name = self.add_number(old_name, new_name)
        new_name = join(dirname(old_name), '{}.mp3'.format(new_name))
        if old_name != new_name:
            print '{0} -> {1}'.format(basename(old_name), basename(new_name))
            move(old_name, new_name)
        else:
            print basename(new_name)

    def rename_titles(self, exclude='', has_num=True):
        for song in self.Songs:
            self.rename_title(song, exclude, has_num)
        self.reload_songs()

    @staticmethod
    def add_number(filename, new_name):
        f = eyed3.load(filename)
        return '{:02d} - {}'.format(f.tag.track_num[0], new_name)

    def cut_first(self, n=1):
        for name in glob(join(self.FileDir, '*p3')):
            new_name = basename(name)[n:]
            move(name, new_name)

    @staticmethod
    def fix_bonus_track(words):
        if len(words) < 2:
            return
        if words[-2].lower() in ['(bonus', '[bonus']:
            words[-2] = '[Bonus'
        if words[-1].lower() in ['track)', 'track]']:
            words[-1] = 'Track]'

    def add_track_numbers(self):
        with open('order.txt') as f:
            dic = {}
            for i, line in enumerate(f.readlines(), 1):
                if len(line) > 4:
                    words = line.strip('\n\t').split('\t')
                    print words
                    key, value = [words[1], int(words[0])] if len(words) > 1 else [words[0], i]
                    dic[key.lower().strip(' \r\n')] = value
            for filename in self.Songs:
                for key, track_number in dic.iteritems():
                    if key.replace('/', '_') in filename.lower():
                        print '{} - {}'.format(track_number, filename.title())
                        mf = eyed3.load(filename)
                        mf.tag.track_num = track_number
                        if not mf.tag.title:
                            mf.tag.title = unicode(key)
                        mf.tag.save()
                        break

    def add_front(self, word='0'):
        for name in glob(join(self.FileDir, '*')):
            new_name = word + basename(name)
            move(name, new_name)


if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('file', nargs='?', default='.')
    p.add_argument('-n', '--execute', action='store_false')
    args = p.parse_args()
    z = Titles(args.file)
    if args.execute:
        z.rename_all()
