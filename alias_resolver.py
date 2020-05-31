"""
The MIT License (MIT)

Copyright (c) 2019-2020 Merlin Wasmann

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

import yaml
from exceptions import AliasError


class AliasResolver:
    def __init__(self, aliases):
        self.aliases = aliases

    @staticmethod
    def from_yaml_file(filename):
        with open(filename, 'r', encoding='utf8') as config:
            return AliasResolver(yaml.load(config, Loader=yaml.Loader))

    def get(self, key, default=None):
        if self.aliases.get(key.lower(), default):
            return self.aliases.get(key.lower(), default)
        else:
            raise AliasError(key)

    def set(self, key, value):
        self.aliases[key.lower()] = value

    def to_yaml_file(self, filename):
        with open(filename, 'w', encoding='utf8') as file:
            yaml.dump(self.aliases, file, Dumper=yaml.Dumper)

    def __str__(self):
        return yaml.dump(self.aliases, Dumper=yaml.Dumper)
