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
import shutil
import zc.buildout

from jinja2 import Environment, PackageLoader, ChoiceLoader, FunctionLoader, FileSystemLoader

try:
    from hashlib import sha1
except ImportError:
    import sha
    def sha1(str):
        return sha.new(str)

import htpasswd

def sibpath(filename):
    return os.path.join(os.path.dirname(__file__), 'templates', filename)

def is_true(val):
    synonyms = (
        'on',
        'true',
        'yes',
        'enabled',
    )
    return val.lower() in synonyms

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

        self.options.setdefault("namevirtualhost", "")

        self.outputdir = os.path.join(self.buildout['buildout']['parts-directory'], self.name)
        self.options.setdefault("passwdfile", os.path.join(self.outputdir, "passwd"))

        if options.get("enhanced-privacy", '').lower() in ('yes', 'true', 'on'):
            options.setdefault("logformat", '"0.0.0.0 %l %u %t \\"%r\\" %>s %b \\"%{Referer}i\\" \\"%{User-agent}i\\""')
        else:
            options.setdefault("logformat", "combined")

        options.setdefault("indexes", "off")

        # Record a SHA1 of the template we use, so we can detect changes in subsequent runs
        self.options["__hashes_template"] = sha1(open(self.options["template"]).read()).hexdigest()

        # Prod the filter if we have one, to fix dependency graph
        # Look into some better way of doing this after jinja2 refactor
        filter = options.get("filter", None)
        if filter:
            buildout[filter]

    def get_requestheader(self):
        vals = {}
        for key in self.options:
            if key.startswith("requestheader."):
                k = key[len('requestheader.'):]
                v = self.options[key]
                vals[k] = v
        return vals

    def get_header(self):
        vals = {}
        for key in self.options:
            if key.startswith("header."):
                k = key[len("header."):]
                v = self.options[key]
                vals[k] = v
        return vals

    def write_jinja_config(self, opt):
        """ Write the config out, using the jinja2 templating method """
        dirname, basename = os.path.split(self.options['template'])

        loader = ChoiceLoader([
            FileSystemLoader(dirname),
            PackageLoader('isotoma.recipe.apache', 'templates'),
            ])

        template = Environment(loader=loader).get_template(basename)
        rendered = template.render(opt)

        cfgfilename = self.options['configfile']
        open(cfgfilename, "w").write(rendered)

    def get_jinja_config(self, opt, template=None):
        def load_template(path):
            if os.path.exists(path):
                return open(path).read()

        loader = ChoiceLoader([
            FunctionLoader(load_template),
            PackageLoader('isotoma.recipe.apache', 'templates'),
            ])

        template = Environment(loader=loader).get_template(template or self.options['template'])
        return template.render(opt)

    def mkpasswd(self, protected_opt):
        passwds = [(x['username'], x['password']) for x in protected_opt]
        if "password" in self.options:
            passwds.append((
                self.options["username"],
                self.options["password"]
            ))

        if passwds:
            pw = htpasswd.HtpasswdFile(self.options['passwdfile'], create=True)
            for u, p in passwds:
                pw.update(u, p)
            pw.save()


    def use_protection(self):
        '''
        Specify multiple URIs for basicauth protection::

            [apache-protected]
            recipe = isotoma.recipe.apache
            protected =
                /path/to/whatever:realm name:username:password
            <SNIP>

        '''
        protected = []
        if self.options.has_key('protected'):
            for l in self.options['protected'].strip().split("\n"):
                l = l.strip()
                protected.append(dict(
                    zip(['uri', 'name', 'username', 'password'],
                        l.split(":"))
                ))

        return protected

    def use_ssl(self):
        ssl = self.options.get("ssl", "auto")

        if ssl == "auto":
            if "sslcert" in self.options:
                return "on"

        if ssl == "only":
            return "only"
        else:
            return is_true(ssl)

    def configure_ssl(self):
        ssldict = {}
        if self.use_ssl():
            # turn a list of sslca's into an actual list
            ssldict["sslca"] = [x.strip() for x in self.options.get("sslca", "").strip().split()]
            ssldict["aliases"] = [x.strip() for x in self.options.get("aliases", "").strip().split()]
            ssldict["redirects"] = [x.strip() for x in self.options.get("redirects", "").strip().split()]

            # grab ssl chain file
            ssldict["sslcachainfile"] = self.options.get("sslcachainfile", "")

        return ssldict

    def configure_auto_www(self, rewrite_list):
        """Appends an auto-www rewrite to the rewrites list"""
        if is_true(self.options.get("auto-www", "False")):
            if self.options.get("sitename").startswith("www."):
                rewrite_list.append(self.options.get("sitename")[4:])
            else:
                rewrite_list.append("www.%s" % self.options.get("sitename"))

    def configure_rewrites(self):
        rewrites = []
        for line in self.options.get('rewrites', '').strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            rewrites.append(
                dict(zip(
                    ['source', 'destination', 'flags'], line.split(";")
                    ))
                 )
        return rewrites

    def configure_static_aliases(self):
        static_aliases = []
        for line in self.options.get('static_aliases', "").strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            static_aliases.append(dict(zip(('location', 'path'), line.split(":"))))

        return static_aliases


class Apache(ApacheBase):

    default_template = "apache.cfg"

    def __init__(self, buildout, name, options):
        super(Apache, self).__init__(buildout, name, options)

        self.options.setdefault("portal", "portal")

    def install(self):
        if not os.path.isdir(self.outputdir):
            os.mkdir(self.outputdir)
        opt = self.options.copy()

        # SSL, if required
        opt = dict(opt.items() + self.configure_ssl().items())

        # Deal with authentication
        opt["protected"] = self.use_protection()

        opt['rewrites'] = self.configure_rewrites()

        # if we have auto-www on, add additional alias:
        self.configure_auto_www(opt["rewrites"])

        opt['requestheader'] = self.get_requestheader()
        opt['header'] = self.get_header()

        if self.options.get('filter', None):
            filter = self.buildout[self.options['filter']]
            opt['filter'] = filter['command']

        self.write_jinja_config(opt)

        # Write the password file
        self.mkpasswd(opt['protected'])

        return [self.outputdir]

    def update(self):
        pass


class ApacheWSGI(ApacheBase):

    default_template = "apache-wsgi.cfg"

    def __init__(self, buildout, name, options):
        
        super(ApacheWSGI, self).__init__(buildout, name, options)
        
        self.outputdir = os.path.join(self.buildout['buildout']['parts-directory'], self.name)
        self.options.setdefault("passwdfile", os.path.join(self.outputdir, "passwd"))
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

        basicauth = self.options.get("basicauth", "False")
        if basicauth:
            if basicauth.lower() in ("yes", "true"):
                opt["basicauth"] = True
            else:
                opt["basicauth"] = False

        opt['protected'] = self.use_protection()

        opt['static_aliases'] = self.configure_static_aliases()

        opt = dict(opt.items() + self.configure_ssl().items())

        opt["rewrites"] = self.configure_rewrites()
        self.configure_auto_www(opt["rewrites"])

        if opt.get('ldapserver', ''):
            # include the ldap config
            opt['ldap_info'] = self.get_jinja_config(opt, template = 'apache-ldap.cfg')
        else:
            opt['ldapserver'] = None

        opt["indexes"] = is_true(self.options.get("indexes", "on"))

        self.write_jinja_config(opt)

        self.mkpasswd(opt['protected'])

        return [outputdir]

class ApacheMaintenance(ApacheBase):

    default_template = "apache-maintenance.cfg"

    def __init__(self, buildout, name, options):
        super(ApacheMaintenance, self).__init__(buildout, name, options)
        options.setdefault("copy-files", "")
        options.setdefault("maintenance_page", "index.html")

    def _should_copy_files(self, src, dest):
        def _sha(filename):
            f = open(filename, 'rb')
            return sha1(f.read())

        def snapshot_directory(directory):
            files = {}
            for dirpath, dirnames, filenames in os.walk(src):
                for filename in filenames:
                    path = os.path.join(dirpath, filename)
                    files[path] = _sha(path)
            return files

        if not os.path.exists(dest):
            return True

        if snapshot_directory(src) != snapshot_directory(dest):
            return True

        return False

    def copy_files(self):
        if self.options.get("copy-files", None):
            # Copy the maintenance page files into parts
            dest = os.path.join(
                self.buildout["buildout"]["parts-directory"],
                self.name,
                'maintenance-pages'
            )

            if self._should_copy_files(self.options.get("copy-files"), dest):
                if os.path.isdir(dest):
                    shutil.rmtree(dest)
                shutil.copytree(self.options.get("copy-files"), dest)

            # Override the document_root
            self.options["document_root"] = dest

            return [dest]

        return []

    def install(self):
        outputdir, path = os.path.split(os.path.realpath(self.options["configfile"]))
        if not os.path.exists(outputdir):
            os.makedirs(outputdir)

        paths = self.copy_files()

        self.write_jinja_config(self.options)
        return paths

    def update(self):
        return self.copy_files()


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
                dict(zip(['domain', 'redirect', 'params'],
                         line.split(";"))
                    ))
            if len(opt['redirects']) >= 1 and opt['redirects'][0].has_key('params'):
                 opt['redirectparams'] = opt['redirects'][0]['params']
        self.write_jinja_config(opt)

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

        self.write_jinja_config(dict(includes=includes))

        return [outputdir]

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

