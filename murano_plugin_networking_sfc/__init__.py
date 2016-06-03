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

import abc

from murano.common import auth_utils
from murano.dsl import session_local_storage
from neutronclient.v2_0 import client
from oslo_config import cfg

from murano_plugin_networking_sfc import config
from murano_plugin_networking_sfc import error

CONF = cfg.CONF


class NeutronClient(object):

    def __init__(self, this):
        self._owner = this.find_owner('io.murano.Environment')

    @classmethod
    def init_plugin(cls):
        cls.CONF = config.init_config(CONF)

    @property
    def _api_client(self):
        region = None
        if self._owner is not None:
            region = self._owner['region']
        return self.create_neutron_client(region)

    @abc.abstractproperty
    def resource_name(self):
        pass

    @property
    def _client(self):
        return getattr(self._api_client, self.resource_name)

    @staticmethod
    @session_local_storage.execution_session_memorize
    def create_neutron_client(region):
        params = auth_utils.get_session_client_parameters(
            service_type='network', conf=CONF, region=region)
        return client.Client(**params)

    def list(self):
        return self._client.list()

    def get_by_id(self, obj_id):
        return self._client.get(obj_id)

    def get_by_name(self, name):
        obj_list = list(self._client.list(filters={'name': name}))
        if not obj_list:
            return None
        if len(obj_list) > 1:
            raise error.AmbiguousNameException(name)
        return obj_list
