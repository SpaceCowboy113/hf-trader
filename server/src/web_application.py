import json

from flask import Flask
from flask_cors import cross_origin
from flask_restful import Api, Resource
from logger import logger
from pyrsistent import PRecord, field
from registries import TradingModelRegistry, TradingRecordRegistry


class Defaults(PRecord):
    web_client_uri = field(type=str, mandatory=True)


def get_defaults(environment: str) -> Defaults:
    '''
    TODO: move get_defaults and get_authentication_keys (in coinbase_adapter.py)
    into a config.py file that handles loading configuration constants.
    '''
    with open('config/default.json', 'r') as reader:
        defaults = json.load(reader)[environment]
        return Defaults.create(defaults)


def get_cross_origin_uri() -> str:
    web_client_uri = get_defaults('production').web_client_uri
    return f'{web_client_uri}*'


class Statistics(Resource):
    def __init__(
        self,
        trading_record_registry: TradingRecordRegistry,
        trading_model_registry: TradingModelRegistry
    ):
        self.trading_record_registry = trading_record_registry
        self.trading_model_registry = trading_model_registry

    @cross_origin(origins=get_cross_origin_uri())
    def get(self):
        '''
        TODO: parameterize 'algorithmic' and 'q-learning' Queries
        '''
        logger.log('/stats/GET')
        algorithmic_record = self.trading_record_registry['algorithmic']
        q_learning_record = self.trading_record_registry['q-learning']
        extrema_finding_record = self.trading_record_registry['extrema-finding']
        return json.dumps({
            'algorithmic': algorithmic_record.serialize(),
            'q-learning': q_learning_record.serialize(),
            'extrema-finding': extrema_finding_record.serialize()
        })


class Transactions(Resource):
    def __init__(
        self,
        trading_record_registry: TradingRecordRegistry,
        trading_model_registry: TradingModelRegistry
    ):
        self.trading_record_registry = trading_record_registry
        self.trading_model_registry = trading_model_registry

    @cross_origin(origins=get_cross_origin_uri())
    def get(self):
        '''
        TODO: parameterize 'algorithmic' and 'q-learning' Queries
        '''
        logger.log('/transactions/GET')
        algorithmic_record = self.trading_record_registry['algorithmic']
        q_learning_record = self.trading_record_registry['q-learning']
        extrema_finding_record = self.trading_record_registry['extrema-finding']
        return json.dumps({
            'algorithmic': algorithmic_record.transaction_window.serialize(),
            'q-learning': q_learning_record.transaction_window.serialize(),
            'extrema-finding': extrema_finding_record.serialize()
        })


def start(
    trading_record_registry: TradingRecordRegistry,
    trading_model_registry: TradingModelRegistry
):
    flask = Flask(__name__)
    api = Api(flask)

    api.add_resource(
        Statistics,
        '/stats',
        resource_class_kwargs={
            'trading_record_registry': trading_record_registry,
            'trading_model_registry': trading_model_registry
        }
    )

    api.add_resource(
        Transactions,
        '/transactions',
        resource_class_kwargs={
            'trading_record_registry': trading_record_registry,
            'trading_model_registry': trading_model_registry
        }
    )

    flask.run(debug=False)
