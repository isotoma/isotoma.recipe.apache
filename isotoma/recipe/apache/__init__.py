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

import warnings
warnings.filterwarnings('ignore', '.*', UserWarning, 'Cheetah.Compiler', 1508)

from Cheetah.Template import Template
from jinja2 import Environment, PackageLoader

import isotoma.recipe.gocaptain as gocaptain

try:
    from hashlib import sha1
except ImportError:
    import sha
    def sha1(str):
        return sha.new(str)

import htpasswd

def sibpath(filename):
    
    main_dir = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(main_dir): return main_dir
    template_dir = os.path.join(os.path.dirname(__file__), 'templates', filename)
    if os.path.exists(template_dir): return template_dir


class ApacheBase(object):

    def __init__(self, buildout, name, options):
        self.buildout = buildout
        self.name = name
        self.options = options

        options.setdefault("template", sibpath(self.default_template))
        options.setdefault("configfile", os.path.join(buildout['buildout']['parts-directory'], name, "apache.cfg"))

        options.setdefault("logdir", "/var/log/apache2")
        options.setdefault("http_port", "80")
        options.setdefault("https_port", "443")

        if options.get("enhanced-privacy", None).lower() in ('yes', 'true', 'on'):
            options.setdefault("logformat", '"0.0.0.0 %l %u %t \\"%r\\" %>s %b \\"%{Referer}i\\" \\"%{User-agent}i\\""')
        else:
            options.setdefault("logformat", "combined")

        # Record a SHA1 of the template we use, so we can detect changes in subsequent runs
        self.options["__hashes_template"] = sha1(open(self.options["template"]).read()).hexdigest()

    def write_config(self, opt):
        template = open(self.options['template']).read()
        cfgfilename = self.options['configfile']
        c = Template(template, searchList = opt)
        open(cfgfilename, "w").write(str(c))

    def write_jinja_config(self, opt):
        """ Write the config out, using the jinja2 templating method """
        cfgfilename = self.options['configfile']
        rendered = self.get_jinja_config(opt)
        open(cfgfilename, "w").write(rendered)

    def get_jinja_config(self, opt, template = None):
        env = Environment(loader = PackageLoader('isotoma.recipe.apache', 'templates'))
        if template:
            template = env.get_template(template)
        else:
            template = env.get_template(self.default_template)
        rendered = template.render(opt)
        return rendered



class Apache(ApacheBase):

    def __init__(self, buildout, name, options):
        if "sslcert" in options:
            self.default_template = "apache-ssl.cfg"
        else:
            self.default_template = "apache.cfg"

        super(Apache, self).__init__(buildout, name, options)

        self.options.setdefault("namevirtualhost", "")
        self.outputdir = os.path.join(self.buildout['buildout']['parts-directory'], self.name)
        self.options.setdefault("passwdfile", os.path.join(self.outputdir, "passwd"))
        self.options.setdefault("portal", "portal")

    def install(self):
        if not os.path.isdir(self.outputdir):
            os.mkdir(self.outputdir)
        opt = self.options.copy()

        # turn a list of sslca's into an actual list
        opt['sslca'] = [x.strip() for x in opt.get("sslca", "").strip().split()]
        opt['aliases'] = [x.strip() for x in opt.get('aliases', '').strip().split()]
        opt['redirects'] = [x.strip() for x in opt.get('redirects', '').strip().split()]

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
                opt['redirects'].append(opt['sitename'][4:])
            else:
                opt['redirects'].append("www.%s" % opt['sitename'])

        opt['rewrites'] = []
        for line in self.options.get('rewrites', '').strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            opt['rewrites'].append(
                dict(zip(
                    ['source', 'destination', 'flags'], line.split(";")
                    ))
                 )

        self.write_config(opt)

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


class ApacheWSGI(ApacheBase):

    def __init__(self, buildout, name, options):
        
        if "sslcert" in options and not "sslonly" in options:
            self.default_template = "apache-wsgi-ssl.cfg"
        elif "sslonly" in options and options['sslonly'].lower() == 'true':
            self.default_template = "apache-wsgi-ssl-only.cfg"
        else:
            self.default_template = "apache-wsgi.cfg"
        
        super(ApacheWSGI, self).__init__(buildout, name, options)
        
        options.setdefault("aliases", "")

    def install(self):
        outputdir, path = os.path.split(os.path.realpath(self.options["configfile"]))
        if not os.path.exists(outputdir):
            os.makedirs(outputdir)

        opt = self.options.copy()
        
        wsgi = opt['wsgi']
        if wsgi[0] == '/':
            # probably not a relative path in this case
            opt['wsgi'] = wsgi
        else:
            # relative path, make it a real path
            opt['wsgi'] = os.path.join(self.buildout['buildout']['bin-directory'], wsgi)

        if self.options["daemon"].lower() in ("yes", "true"):
            opt["daemon"] = True
        else:
            opt["daemon"] = False

        opt ['aliases'] = []
        for line in self.options['aliases'].strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            opt['aliases'].append(
                dict(zip(('location', 'path'), line.split(":"))
                ))

        # SSL BELOW

        # turn a list of sslca's into an actual list
        opt['sslca'] = [x.strip() for x in opt.get("sslca", "").strip().split()]
        opt['redirects'] = [x.strip() for x in opt.get('redirects', '').strip().split()]

        # if we have auto-www on, add additional alias:
        if self.options.get("auto-www", "False") == "True":
            if opt['sitename'].startswith("www."):
                opt['redirects'].append(opt['sitename'][4:])
            else:
                opt['redirects'].append("www.%s" % opt['sitename'])
                
        if opt.get('ldapserver', ''):
            # include the ldap config
            opt['ldap_info'] = self.get_jinja_config(opt, template = 'apache-ldap.cfg')
        else:
            opt['ldapserver'] = None

        self.write_config(opt)

        return [outputdir]


class Redirect(ApacheBase):

    default_template = "apache-redirect.cfg"

    def __init__(self, buildout, name, options):
        super(Redirect, self).__init__(buildout, name, options)

    def install(self):
        outputdir, path = os.path.split(os.path.realpath(self.options["configfile"]))
        if not os.path.exists(outputdir):
            os.makedirs(outputdir)

        opt = self.options.copy()
        opt['redirects'] = []
        for line in self.options['redirects'].strip().split("\n"):
            line = line.strip()
            opt['redirects'].append(
                dict(zip(['domain', 'redirect'],
                         line.split(";"))
                    ))

        self.write_config(opt)

        return [outputdir]

    def update(self):
        pass


class Includes(ApacheBase):

    default_template = "includes.cfg"

    def install(self):
        outputdir, path = os.path.split(os.path.realpath(self.options["configfile"]))
        if not os.path.exists(outputdir):
            os.makedirs(outputdir)

        includes = []
        for line in self.options['includes'].strip().split("\n"):
            line = line.strip()
            if line:
                includes.append(line)

        self.write_config(dict(includes=includes))

        return [outputdir]

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

class SinglePage(ApacheBase):
    """ Used for generating emergency/maintenance page configs """
    
    default_template = "apache-single.cfg"
    
    def install(self):
        outputdir, path = os.path.split(os.path.realpath(self.options["configfile"]))
        if not os.path.exists(outputdir):
            os.makedirs(outputdir)
            
        opt = self.options.copy()
        
        file_path = opt['file_path']
        if file_path[0] == '/':
            # probably not a relative path in this case
            opt['file_path'] = file_path
        else:
            # relative path, make it a real path
            opt['file_path'] = os.path.join(self.buildout['buildout']['bin-directory'], file_path)
            
        
        # this can't be missing, but it can be empty
        if not opt.has_key('listen'):
            opt['listen'] = ''
            
        # we might need to listen on multiple interfaces (if the whole lot has gone down)
        opt['interfaces'] = []
        for line in self.options['interfaces'].strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            opt['interfaces'].append(
                dict(zip(('interface', 'port', 'servername', 'ssl'), line.split(":"))
                ))

        opt['sslca'] = [x.strip() for x in opt.get("sslca", "").strip().split()]
            
        self.write_jinja_config(opt)
        
        return [outputdir]
 
class Ldap(ApacheBase):
    """Configure stanza for protecting dir using LDAP"""

    def __init__(self, buildout, name, options):
        self.buildout = buildout
        self.name = name
        self.options = options
        self.default_template = "apache-ldap.cfg"
        options.setdefault("template", sibpath(self.default_template))


    def install(self):
        outputdir, path = os.path.split(os.path.realpath(self.options["configfile"]))
        if not os.path.exists(outputdir):
            os.makedirs(outputdir)
            
        opt = self.options.copy()
        print self.default_template
        self.write_jinja_config(opt)  

        return [outputdir]

