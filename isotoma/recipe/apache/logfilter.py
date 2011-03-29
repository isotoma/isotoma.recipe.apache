# Copyright 2010 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import optparse, os, stat, sys

p = optparse.OptionParser()
p.add_option("--partial", action="store_true")
opts, args = p.parse_args()


class ReopeningFile(object):

    def __init__(self, file):
        self.file = None
        self.fp = None
        self.st_dev = None
        self.st_ino = None

    def stat(self):
        s = os.stat(self.file)
        return s[ST_DEV], s[ST_INO]

    def reopen(self):
        if self.fp:
            self.fp.flush()
            self.fp.close()

        self.fp = open(self.file, 'a')
        self.st_dev, self.st_ino = self.stat()

    def changed(self):
        st_dev, st_ino = self.stat()
        if self.st_dev != st_dev or st_ino != self.st_ino:
            return True
        return False

    def write(self, data):
        if self.changed():
            self.reopen()
        self.fp.write(data)


def main():
    log = ReopeningFile(args[0])

    # loop to sit reading from apache
    line = sys.stdin.readline()
    while line != '':
        # replace the last 2 octets with 0
        # this is done this way as its simple and less prone to failure...
        try:
            ip, rest = line.split(' ', 1)

            if opts.partial:
                octet1, octet2 = ip.split('.', 2)[:2]
                log.write('%s.%s.0.0 %s' % (octet1, octet2, rest))
            else:
                log.write('0.0.0.0 %s' % rest)
        except:
            pass

        line = sys.stdin.readline()

