# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os

import gunicorn.app.base

GUNICORN_OPTIONS_SEPARATOR_ENV = "GUNICORN_OPTIONS_SEPARATOR"
"""The name of the env variable that holds a separator of the Gunicorn options."""
GUNICORN_OPTIONS_ENV = "GUNICORN_OPTIONS"
"""The name of the env variable that holds Gunicorn options in a key=value format
where each option is separated from the other one with a GUNICORN_OPTIONS_SEPARATOR 
(or `,`) by default.
"""


def _gunicorn_env_options():
    """Parses Gunicorn options provided through environment variable if any are provided.

    The Gunicorn options are specified using `GUNICORN_OPTIONS_<option-name>` formatted options
    that can override the standard provided options if specified.
    """
    gunicorn_options = os.getenv(GUNICORN_OPTIONS_ENV)
    if not gunicorn_options:
        return {}
    options_separator = os.getenv(GUNICORN_OPTIONS_SEPARATOR_ENV, ",")
    options = gunicorn_options.split(options_separator)
    result = {}
    for option in options:
        option_config = option.split("=", maxsplit=2)
        if len(option_config) == 2:
            key, value = option_config
        elif len(option_config) == 3:
            key, value, value_type = option_config
            if value_type == "int":
                value = int(value)
            elif value_type == "float":
                value = float(value)
            elif value_type == "bool":
                value = bool(value)
        else:
            raise TypeError(
                f"Gunicorn option config must be of format key=value(=type), but was: {option}"
            )
        result[key] = value
    return result


class GunicornApplication(gunicorn.app.base.BaseApplication):
    def __init__(self, app, host, port, debug, **options):
        self.options = {
            "bind": "%s:%s" % (host, port),
            "workers": 1,
            "threads": 1024,
            "timeout": 0,
            "loglevel": "error",
            "limit_request_line": 0,
        }
        self.options.update(options)
        self.options.update(_gunicorn_env_options())
        self.app = app
        super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            self.cfg.set(key, value)

    def load(self):
        return self.app
