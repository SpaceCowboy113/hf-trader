from flask import Flask
from flask_restful import Api, Resource
from registries import TradingRecordRegistry, TradingModelRegistry
from logger import logger


class Statistics(Resource):
    def __init__(
        self,
        trading_record_registry: TradingRecordRegistry,
        trading_model_registry: TradingModelRegistry
    ):
        self.trading_record_registry = trading_record_registry
        self.trading_model_registry = trading_model_registry

    def get(self):
        logger.log('/stats/GET')
        return self.trading_record_registry['algorithmic'].serialize()
        # return 'statistics', 1234


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

    flask.run(debug=True)
