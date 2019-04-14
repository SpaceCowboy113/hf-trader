import React from 'react';
import ReactDOM from 'react-dom';
import App from './components/app';
import * as serviceWorker from './service-worker';
import ObservableMap from './state/observable-map';
import { TradingModel, TradingRecord } from './state/trading-state';
import './style/index.css';

const tradingRecordRegistry = new ObservableMap<TradingRecord>();
const tradingModelRegistry = new ObservableMap<TradingModel>();

ReactDOM.render(
    <App
        tradingRecordRegistry={tradingRecordRegistry}
        tradingModelRegistry={tradingModelRegistry}
    />,
    document.getElementById('root'),
);

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: http://bit.ly/CRA-PWA
serviceWorker.unregister();
