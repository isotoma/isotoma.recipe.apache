Apache buildout recipe
======================

This package provides buildout_ recipes for the configuration of apache.  This
has a number of features that we have found useful in production, such as
support for long CA chains, htpasswd authentication protection and the support
for optional templates provided with the buildout.

We use the system apache, so this recipe will not install apache for you.  If
you wish to install apache, use `zc.recipe.cmmi`_ perhaps.

.. _buildout: http://pypi.python.org/pypi/zc.buildout
.. _`zc.recipe.cmmi`: http://pypi.python.org/pypi/zc.recipe.cmmi


Mandatory Parameters
--------------------

interface
    The IP address of the interface on which to listen
sitename
    The name of the site, used to identify the correct virtual host
serveradmin
    The email address of the administrator of the server
proxyport
    The port to which requests are forwarded

Optional Parameters
-------------------

realm
    The name of the HTTP Authentication realm, if you wish to password protect this site
passwdfile
    The filename of the htpasswd file to secure the realm, defaults to "passwd" in the part directory
username
    The username used in the htpasswd file
allowpurge
    The IP address of a server that is permitted to send PURGE requests to this server
portal
    The name of the portal object in the zope server, defaults to "portal"
template
    The filename of the template file to use, if you do not wish to use the default
configfile
    The name of the config file written by the recipe, defaults to "apache.cfg" in the part directory
sslca
    A list of full pathnames to certificate authority certificate files
sslcert
    The full pathname of the ssl certificate, if required
sslkey
    The full pathname of the key for the ssl certificate
auto-www
    If true, the recipe will have a ServerAlias for www.${sitename}. If your sitename already has a www prefix, the alias will be sitename with the prefix trimmed.
logdir
    Where to store apache logs (Default: /var/log/apache2)

Standalone httpd
----------------

If you want to start and stop apache without needing root and can run apache on a high port, this recipe is for you.

user
    The user that will be running this apache
group
    The group that apache will run under
listen
    Any high ports this apache will listen on
vhosts
    A list of paths to the config you would normally have in /etc/apache2/sites-enabled

Use ./bin/httpd start|stop to control the server, where httpd is the name of the part that is using the recipe.

Repository
----------

This software is available from our `recipe repository`_ on github.

.. _`recipe repository`: http://github.com/isotoma/recipes

License
-------

Copyright 2010 Isotoma Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


