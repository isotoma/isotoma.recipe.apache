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
import isotoma.recipe.gocaptain as gocaptain

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

    def __init__(self, buildout, name, options):
        self.name = name
        self.options = options
        self.buildout = buildout
        if "sslcert" in options:
            default_template = "apache-ssl.cfg"
        else:
            default_template = "apache.cfg"
        self.outputdir = os.path.join(self.buildout['buildout']['parts-directory'], self.name)
        self.options.setdefault("logdir", "/var/log/apache2")
        self.options.setdefault("http_port", "80")
        self.options.setdefault("https_port", "443")
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
        opt['aliases'] = [x.strip() for x in opt.get('aliases', '').strip().split()]
        opt['protected'] = []
        if 'protected' in self.options:
            for l in self.options['protected'].strip().split("\n"):
                l = l.strip()
                opt['protected'].append(
                    dict(zip(['uri', 'name', 'username', 'password'], 
                             l.split(":"))
                    ))

        # if we have auto-www on, add additional alias:
        if self.options.get("auto-www", "False") == "True":
            if opt['sitename'].startswith("www."):
                opt['aliases'].append(opt['sitename'][4:])
            else:
                opt['aliases'].append("www.%s" % opt['sitename'])

        template = open(self.options['template']).read()
        cfgfilename = self.options['configfile']
        c = Template(template, searchList = opt)
        open(cfgfilename, "w").write(str(c))
        passwds = [(x['username'], x['password']) for x in opt['protected']]
        if "password" in self.options:
            passwds.append((self.options["username"], self.options["password"]))
        self.mkpasswd(passwds)
        return [self.outputdir]

    def mkpasswd(self, passwds):
        if passwds:
            pw = htpasswd.HtpasswdFile(self.options['passwdfile'], create=True)
            for u, p in passwds:
                pw.update(u, p)
            pw.save()

    def update(self):
        pass


class Standalone(object):

    def __init__(self, buildout, name, options):
        self.buildout = buildout
        self.name = name
        self.options = options

        for opt in ("user", "group", "listen"):
            if not opt in self.options:
                raise ValueError("'%s' must be set" % opt)
                #raise UserError("'%s' must be set" % opt)

        self.outputdir = os.path.join(self.buildout['buildout']['parts-directory'], self.name)
        self.options.setdefault("template", sibpath("standalone.cfg"))
        self.options.setdefault("configfile", os.path.join(self.outputdir, "standalone.cfg"))

        self.options.setdefault("executable", "/usr/sbin/apache2")
        vardir = os.path.join(self.buildout['buildout']['directory'], "var")
        self.options.setdefault("pidfile", os.path.join(vardir, "%s.pid" % self.name))
        self.options.setdefault("lockfile", os.path.join(vardir, "%s.lock" % self.name))

        self.options.setdefault("errorlog", os.path.join(vardir, "%s_error.log" % self.name))
        self.options.setdefault("customlog", os.path.join(vardir, "%s_other_vhosts_access.log" % self.name))

        # Record a SHA1 of the template we use, so we can detect changes in subsequent runs
        self.options["__hashes_template"] = sha1(open(self.options["template"]).read()).hexdigest()

    def install(self):
        if not os.path.isdir(self.outputdir):
            os.mkdir(self.outputdir)
            self.options.created(self.outputdir)

        opt = self.options.copy()

        # Tidy up lists
        opt['vhosts'] = [x.strip() for x in self.options.get("vhosts").strip().split()]
        opt['listen'] = [x.strip() for x in self.options.get("listen").strip().split()]

        template = open(self.options['template']).read()
        c = Template(template, searchList = opt)
        cfgfilename = self.options['configfile']
        open(cfgfilename, "w").write(str(c))
        self.options.created(cfgfilename)

        self.runscript()

        return self.options.created()

    def runscript(self):
        target=os.path.join(self.buildout["buildout"]["bin-directory"],self.name)
        args = '-f "%s"' % self.options["configfile"]
        gc = gocaptain.Automatic()
        gc.write(open(target, "wt"),
                 daemon=self.options['executable'],
                 args=args,
                 pidfile=self.options["pidfile"],
                 name=self.name,
                 description="%s daemon" % self.name)
        os.chmod(target, 0755)
        self.options.created(target)

    def update(self):
        pass


