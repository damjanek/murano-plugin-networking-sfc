#    Copyright 2016 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import re


def underscore_to_camel_case(name):
    """Converts lower case underscore names to camel case."""
    return re.sub(
        r'(.)_([a-z])',
        lambda m: m.group(1) + m.group(2).upper(),
        name)


def camel_case_to_underscore(name):
    """Converts camel case names to underscore lower case"""
    return re.sub(
        '([a-z])([A-Z])',
        lambda m: m.group(1) + '_' + m.group(2).lower(),
        name)


def params_converter(func, converter):
    def wrapper(*args, **kwargs):
        new_kwargs = {}
        for key in kwargs:
            new_key = converter(key)
            new_kwargs[new_key] = kwargs[key]
        return func(*args, **new_kwargs)
    return wrapper
