import React from 'react';
import ReactDOM from 'react-dom';
import App from './app';
import ObservableMap from '../state/observable-map';
import { TradingModel, TradingRecord } from '../state/trading-state';

it('renders without crashing', () => {
  const div = document.createElement('div');
  const tradingRecordRegistry = new ObservableMap<TradingRecord>();
  const tradingModelRegistry = new ObservableMap<TradingModel>();
  ReactDOM.render(<App
      tradingRecordRegistry={tradingRecordRegistry}
      tradingModelRegistry={tradingModelRegistry}
    />,
    div,
  );
  ReactDOM.unmountComponentAtNode(div);
});
