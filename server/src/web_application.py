import json

from flask import Flask
from flask_cors import CORS, cross_origin
from flask_restful import Api, Resource
from logger import logger
from registries import TradingModelRegistry, TradingRecordRegistry

# TODO: move into a configuration file
CLIENT_URI = 'http://localhost:3000'


class Statistics(Resource):
    def __init__(
        self,
        trading_record_registry: TradingRecordRegistry,
        trading_model_registry: TradingModelRegistry
    ):
        self.trading_record_registry = trading_record_registry
        self.trading_model_registry = trading_model_registry

    @cross_origin(origins=f'{CLIENT_URI}*')
    def get(self):
        '''
        TODO: parameterize 'algorithmic' and 'q-learning' Queries
        '''
        logger.log('/stats/GET')
        algorithmic_record = self.trading_record_registry['algorithmic']
        q_learning_record = self.trading_record_registry['q-learning']
        return json.dumps({
            'algorithmic': algorithmic_record.serialize(),
            'q-learning': q_learning_record.serialize(),
        })


class Transactions(Resource):
    def __init__(
        self,
        trading_record_registry: TradingRecordRegistry,
        trading_model_registry: TradingModelRegistry
    ):
        self.trading_record_registry = trading_record_registry
        self.trading_model_registry = trading_model_registry

    @cross_origin(origins=f'{CLIENT_URI}*')
    def get(self):
        '''
        TODO: parameterize 'algorithmic' and 'q-learning' Queries
        '''
        logger.log('/transactions/GET')
        algorithmic_record = self.trading_record_registry['algorithmic']
        q_learning_record = self.trading_record_registry['q-learning']
        return json.dumps({
            'algorithmic': algorithmic_record.transaction_window.serialize(),
            'q-learning': q_learning_record.transaction_window.serialize(),
        })


def start(
    trading_record_registry: TradingRecordRegistry,
    trading_model_registry: TradingModelRegistry
):
    flask = Flask(__name__)
    CORS(flask)  # do i really need this line with the decorator?
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

    flask.run(debug=True)
