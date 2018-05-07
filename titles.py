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


class Titles(Keys, Mouse):
    def __init__(self, file_dir):
        self.FileDir = file_dir
        self.Band = self.get_band()
        self.Album = self.get_album()
        Keys.__init__(self)
        Mouse.__init__(self)

    def get_band(self):
        band = basename(dirname(realpath(self.FileDir)))
        return self.get_album() if band == 'Music' else band

    def get_album(self):
        return basename(realpath(self.FileDir))

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

    def rename_title(self, name, exclude):
        excl_str = exclude
        exclude = [excl_str, self.Band, self.Album]
        old_name = name
        if isdir(name):
            print name, 'is a dir'
            for title in glob(join(name, '*')):
                self.rename_title(title, excl_str)
            return
        name = basename(name).replace('.mp3', '').replace('.Mp3', '')
        for word in exclude:
            if len(name) > len(word) * 2:
                name = name.replace(word, '', 1)
        for ending in ['.ini', 'jpg']:
            if ending in name:
                return
        data = [word.strip(' _') for word in split('[ ._-]', name)]
        data = [word if word.isupper() else word.title() for word in data]
        data = filter(lambda x: x, data)
        start_index = data.index(next(word for word in data if word.isdigit()))
        new_name = ' '.join([' - '.join(data[start_index:start_index + 2]).strip(' ')] + data[start_index + 2:])
        new_name = join(dirname(old_name), new_name) + '.mp3'
        if old_name != new_name:
            print '{0} -> {1}'.format(basename(old_name), basename(new_name))
            move(old_name, new_name)
        else:
            print basename(new_name)

    def rename_titles(self, exclude=''):
        for name in glob(join(self.FileDir, '*')):
            self.rename_title(name, exclude)

    def cut_first(self, n=1):
        for name in glob(join(self.FileDir, '*')):
            new_name = basename(name)[n:]
            move(name, new_name)

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
