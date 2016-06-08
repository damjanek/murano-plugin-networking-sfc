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
    plural_actions = ['list']

    @abc.abstractproperty
    def name(self):
        pass

    @abc.abstractproperty
    def plural_name(self):
        pass

    def __init__(self, client):
        self._client = client

    def _get_neutron_function(self, resource_name, action):
        function_name = '{0}_{1}'.format(action, resource_name)
        return getattr(self._client, function_name)

    def _prepare_request(self, params):
        return {self.name: params}

    def create(self, **kwargs):
        request = self._prepare_request(kwargs)
        response = self._get_neutron_function(self.name, 'create')(request)
        return response[self.name]

    def list(self):
        return self._get_neutron_function(self.plural_name, 'list')()

    def show(self, id_):
        try:
            return self._get_neutron_function(self.name, 'show')(id_)
        except n_err.NotFound as exc:
            raise error.NotFound(exc.message)

    def update(self, id_, **kwargs):
        kwargs['id'] = id_
        request = self._prepare_request(kwargs)
        try:
            response = self._get_neutron_function(self.name, 'update')(request)
        except n_err.NotFound as exc:
            raise error.NotFound(exc.message)
        return response[self.name]

    def delete(self, id_):
        try:
            return self._get_neutron_function(self.name, 'delete')(id_)
        except n_err.NotFound as exc:
            raise error.NotFound(exc.message)


class PortChain(_BaseResourceWrapper):

    name = 'port_chain'
    plural_name = '{0}s'.format(name)


class PortPair(_BaseResourceWrapper):

    name = 'port_pair'
    plural_name = '{0}s'.format(name)


class PortPairGroup(_BaseResourceWrapper):

    name = 'port_pair_group'
    plural_name = '{0}s'.format(name)


class FlowClassifier(_BaseResourceWrapper):

    name = 'flow_classifier'
    plural_name = '{0}s'.format(name)


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


class NetworkinfSFCClient(_BaseNeutronClient):

    resources = [
        PortChain,
        PortPair,
        PortPairGroup,
        FlowClassifier,
    ]

    def __init__(self, this):
        super(NetworkinfSFCClient, self).__init__(this)

        self._methods = {}
        for rs_cls in self.resource_classes:
            resource = rs_cls(self.client)
            for action in resource.allowed_actions:
                if action in resource.pluial_actions:
                    name = resource.plural_name
                else:
                    name = resource.name
                name = '{0}_{1}'.format(action, name)
                self._methods[name] = common.params_converter(
                    getattr(resource, action),
                    common.camel_case_to_underscore)

    def __getattr__(self, name):
        name = common.camel_case_to_underscore(name)
        try:
            return self._methods[name]
        except KeyError:
            raise AttributeError(
                "'{0}' object has no attribute '{1}'".format(
                    self.__class__.__name__, name))
