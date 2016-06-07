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

from murano.common import auth_utils
from murano.dsl import session_local_storage
from neutronclient.common import exceptions as n_err
from neutronclient.v2_0 import client
from oslo_config import cfg

from murano_plugin_networking_sfc import config
from murano_plugin_networking_sfc import error

CONF = cfg.CONF

DEFAULT = object()


class NetworkingSFCClient(object):

    def __init__(self, this):
        self._owner = this.find_owner('io.murano.Environment')

    @classmethod
    def init_plugin(cls):
        cls.CONF = config.init_config(CONF)

    @property
    def _client(self):
        region = None
        if self._owner is not None:
            region = self._owner['region']
        return self._get_client(region)

    @staticmethod
    @session_local_storage.execution_session_memoize
    def _get_client(region):
        params = auth_utils.get_session_client_parameters(
            service_type='network', conf=CONF, region=region)
        return client.Client(**params)

    @staticmethod
    def _prepare_request(resource_name, **kwargs):
        params = {}
        for k, v in kwargs.items():
            if v is not DEFAULT:
                params[k] = v
        return {resource_name: params}

    def create_port_chain(
            self, port_pair_groups, flow_classifiers=DEFAULT,
            name=DEFAULT, description=DEFAULT, chain_parameters=DEFAULT):
        request = self._prepare_request(
            'port_chain', port_pair_groups=port_pair_groups,
            flow_classifiers=flow_classifiers, name=name,
            description=description, chain_parameters=chain_parameters)
        response = self._client.create_port_chain(request)
        return response['port_chain']

    def delete_port_chain(self, id_):
        try:
            self._client.delete_port_chain(id_)
        except n_err.NotFound as exc:
            raise error.NotFoundError(exc.message)

    def list_port_chains(self):
        response = self._client.list_port_chains()
        return response['port_chains']

    def show_port_chain(self, id_):
        response = self._client.show_port_chain(id_)
        return response['port_chain']

    def update_port_chain(
            self, id_, port_pair_groups=DEFAULT, name=DEFAULT,
            description=DEFAULT):
        request = self._prepare_request(
            'port_chain', id=id_, port_pair_groups=port_pair_groups, name=name,
            description=description)
        response = self._client.update_port_chain(request)
        return response['port_chain']

    def create_port_pair(
            self, ingress, egress, name=DEFAULT, description=DEFAULT,
            service_function_parameters=DEFAULT):
        request = self._prepare_request(
            'port_pair', ingress=ingress, egress=egress,
            name=name, description=description,
            service_function_parameters=service_function_parameters)
        response = self._client.create_port_pair(request)
        return response['port_pair']

    def delete_port_pair(self, id_):
        try:
            self._client.delete_port_pair(id_)
        except n_err.NotFound as exc:
            raise error.NotFoundError(exc.message)

    def list_port_pairs(self):
        response = self._client.list_port_pairs()
        return response['port_pairs']

    def show_port_pair(self, id_):
        response = self._client.show_port_pair(id_)
        return response['port_pair']

    def update_port_pair(self, id_, name=DEFAULT, description=DEFAULT):
        request = self._prepare_request(
            'port_pair', id=id_, name=name, description=description)
        response = self._client.update_port_pair(request)
        return response['port_pair']

    def create_port_pair_group(
            self, port_pairs, name=DEFAULT, description=DEFAULT):
        request = self._prepare_request(
            'port_pair_group', port_pairs=port_pairs, name=name,
            description=description)
        response = self._client.create_port_pair_group(request)
        return response['port_pair_group']

    def delete_port_pair_group(self, id_):
        try:
            self._client.delete_port_pair_group(id_)
        except n_err.NotFound as exc:
            raise error.NotFoundError(exc.message)

    def list_port_pair_groups(self):
        response = self._client.list_port_pair_groups()
        return response['port_pair_groups']

    def show_port_pair_group(self, id_):
        response = self._client.show_port_pair_group(id_)
        return response['port_pair_group']

    def update_port_pair_group(
            self, id_, port_pairs=DEFAULT, name=DEFAULT, description=DEFAULT):
        request = self._prepare_request(
            'port_pair_group', id=id_, port_pairs=port_pairs,
            name=name, description=description)
        response = self._client.update_port_pair_group(request)
        return response['port_pair_group']
