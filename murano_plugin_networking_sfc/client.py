import abc

import six

from murano.common import auth_utils
from murano.dsl import session_local_storage
from neutronclient.common import exceptions as n_err
from neutronclient.v2_0 import client as n_client
from oslo_config import cfg

from murano_plugin_networking_sfc import config
from murano_plugin_networking_sfc import common
from murano_plugin_networking_sfc import error


CONF = cfg.CONF


class _BaseResourceWrapper(object):

    allowed_actions = ['create', 'list', 'show', 'update', 'delete']

    @abc.abstractproperty
    def name(self):
        pass

    @abc.abstractproperty
    def plural_name(self):
        pass

    @abc.abstractproperty
    def params(self):
        pass

    def __init__(self, client):
        self._client = client

    def _get_neutron_function(self, resource_name, action):
        function_name = '{0}_{1}'.format(action, resource_name)
        return getattr(self._client, function_name)

    def _prepare_request(self, action, params):
        for key, rules in six.iteritems(self.params):
            if key not in params:
                if 'required' in rules:
                    raise error.ParameterMissing(
                        "Required parameter '{0}' is missing".format(key))
                else:
                    continue

            if action not in rules:
                raise error.ActionNotAllowed(
                    "Action '{0}' is not allowed for parameter '{1}'".format(
                        action, key))

        return {self.name: params}

    def create(self, **kwargs):
        request = self._prepare_request('create', kwargs)
        response = self._get_neutron_function(self.name, 'create')(request)
        return response[self.name]

    def list(self):
        return self._get_neutron_function(self.plural_name, 'list')()

    def show(self, id_):
        return self._get_neutron_function(self.name, 'show')(id_)

    def update(self, id_, **kwargs):
        kwargs['id'] = id_
        request = self._prepare_request(self.name, 'update', kwargs)
        response = self._get_neutron_function(self.name, 'update')(request)
        return response[self.name]

    def delete(self, id_):
        return self._get_neutron_function(self.name, 'delete')(id_)


class PortChain(_BaseResourceWrapper):

    name = 'port_chain'
    plural_name = '{0}s'.format(name)
    params = {
        'name': ['create', 'update'],
        'description': ['create', 'update'],
        'port_pair_groups': ['create', 'update', 'required'],
        'flow_classifiers': ['create', 'update'],
        'chain_parameters': ['create'],
    }


class PortPair(_BaseResourceWrapper):

    name = 'port_pair'
    plural_name = '{0}s'.format(name)
    params = {
        'name': ['create', 'update'],
        'description': ['create', 'update'],
        'ingress': ['create', 'required'],
        'egress': ['create', 'required'],
        'service_function_parameters': ['create'],
    }


class PortPairGroup(_BaseResourceWrapper):

    name = 'port_pair_group'
    plural_name = '{0}s'.format(name)
    params = {
        'name': ['create', 'update'],
        'description': ['create', 'update'],
        'port_pairs': ['create', 'update', 'required'],
    }


class FlowClassifier(_BaseResourceWrapper):

    name = 'flow_classifier'
    plural_name = '{0}s'.format(name)
    params = {
        'name': ['create', 'update'],
        'description': ['create', 'update'],
        'ethertype': ['create'],
        'protocol': ['create'],
        'source_port_range_min': ['create'],
        'source_port_range_max': ['create'],
        'destination_port_range_min': ['create'],
        'destination_port_range_max': ['create'],
        'source_ip_prefix': ['create'],
        'destination_ip_prefix': ['create'],
        'logical_source_port': ['create'],
        'logical_destination_port': ['create'],
        'l7_parameters': ['create']
    }


class _BaseNeutronClient(object):
    def __init__(self, this):
        self._owner = this.find_owner('io.murano.Environment')

    @classmethod
    def init_plugin(cls):
        cls.CONF = config.init_config(CONF)

    @property
    def client(self):
        region = None
        if self._owner is not None:
            region = self._owner['region']
        return self._get_client(region)

    @staticmethod
    @session_local_storage.execution_session_memoize
    def _get_client(region):
        params = auth_utils.get_session_client_parameters(
            service_type='network', conf=CONF, region=region)
        return n_client.Client(**params)

    def __getattr__(self, item):
        item = common.camel_case_to_underscore(item)

        return common.params_converter(func, common.camel_case_to_underscore)


class NetworkinfSFCClient(_BaseNeutronClient):

    resources = [
        PortChain,
        PortPair,
        PortPairGroup,
        FlowClassifier,
    ]

    def __init__(self, this):
        super(NetworkinfSFCClient, self).__init__(this)

        self._resource_wrappers = []
        for resource_cls in self.resources:
            self._resource_wrappers.append(resource_cls(self.client))


