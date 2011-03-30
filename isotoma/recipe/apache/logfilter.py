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

import optparse, os, stat, sys, re

exp = r'(?<![\d\.])(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?![\d\.])'

p = optparse.OptionParser()
p.add_option("--partial", action="store_true")
opts, args = p.parse_args()


class ReopeningFile(object):

    def __init__(self, file):
        self.file = file
        self.fp = None
        self.st_dev = None
        self.st_ino = None
        self.reopen()

    def stat(self):
        s = os.stat(self.file)
        return s[stat.ST_DEV], s[stat.ST_INO]

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
        self.fp.flush()


def regex_strip_ip(match):
    return "0.0.0.0"

def regex_partial_ip(match):
    octets = match.group(0).split('.')
    return ".".join((octets[0], octets[1], '0', '0'))

def main():
    log = ReopeningFile(args[0])

    ip_regex = re.compile(exp)

    # loop to sit reading from apache
    line = sys.stdin.readline()
    while line != '':
        if opts.partial:
            filter = regex_partial_ip
        else:
            filter = regex_strip_ip

        log.write(ip_regex.sub(filter, line))

        line = sys.stdin.readline()

