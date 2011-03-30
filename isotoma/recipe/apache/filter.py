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

import os, sys
from zc.buildout import easy_install

class Filter(object):

    def __init__(self, buildout, name, options):
        self.name = name
        self.options = options
        self.buildout = buildout

        command = [os.path.join(self.buildout["buildout"]["bin-directory"], self.name)]

        if options.get("partial", "").lower() in ("yes", "on", "true"):
            command.append("--partial")

        # Export the incantation to embed in apache templates
        options["command"] = " ".join(command)

        self.installed = []

    def install(self):
        path = self.buildout["buildout"]["bin-directory"]
        egg_paths = [
            self.buildout["buildout"]["develop-eggs-directory"],
            self.buildout["buildout"]["eggs-directory"],
            ]

        ws = easy_install.working_set(["isotoma.recipe.apache"], sys.executable, egg_paths)
        easy_install.scripts([(self.name, "isotoma.recipe.apache.logfilter", "main")], ws, sys.executable, path)

        self.installed.append(os.path.join(path, self.name))

        return self.installed

