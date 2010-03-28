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

import logging
import os
import zc.buildout
from Cheetah.Template import Template

try:
    from hashlib import sha1
except ImportError:
    import sha
    def sha1(str):
        return sha.new(str)

import htpasswd

def sibpath(filename):
    return os.path.join(os.path.dirname(__file__), filename)

class Apache(object):

    template = os.path.join(os.path.dirname(__file__), "apache.cfg")
    ssltemplate = os.path.join(os.path.dirname(__file__), "apache-ssl.cfg")

    def __init__(self, buildout, name, options):
        self.name = name
        self.options = options
        self.buildout = buildout
        if "sslcert" in options:
            default_template = "apache-ssl.cfg"
        else:
            default_template = "apache.cfg"
        self.outputdir = os.path.join(self.buildout['buildout']['directory'], self.name)
        self.options.setdefault("template", sibpath(default_template))
        self.options.setdefault("passwdfile", os.path.join(self.outputdir, "passwd"))
        self.options.setdefault("configfile", os.path.join(self.outputdir, "apache.cfg"))
        self.options.setdefault("portal", "portal")

        # Record a SHA1 of the template we use, so we can detect changes in subsequent runs
        self.options["__hashes_template"] = sha1(open(self.options["template"]).read()).hexdigest()

    def install(self):
        if not os.path.isdir(self.outputdir):
            os.mkdir(self.outputdir)
        opt = self.options.copy()
        # turn a list of sslca's into an actual list
        opt['sslca'] = [x.strip() for x in opt.get("sslca", "").strip().split()]
        template = open(self.options['template']).read()
        cfgfilename = self.options['configfile']
        c = Template(template, searchList = opt)
        open(cfgfilename, "w").write(str(c))
        self.mkpasswd()
        return [self.outputdir]

    def mkpasswd(self):
        if "password" in self.options:
            pw = htpasswd.HtpasswdFile(self.options['passwdfile'], create=True)
            pw.update(self.options["username"], self.options["password"])
            pw.save()
        
    def update(self):
        pass
