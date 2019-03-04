import React, { Component } from 'react';
import logo from './logo.svg';
import './app.css';
import { LineChart, Line, CartesianGrid, XAxis, YAxis } from 'recharts';
import TradesLineChart from './trades-line-chart';
import { Signal } from 'micro-signals';
import ObservableMap from './observable-map';
import { TradingRecordRegistry, TradingModelRegistry, TradingModel, TradingRecord, getExchangeRate } from './trading-state';
import { Result } from './result';
import TradingRecordView from './trading-record-view';

interface AppProps {
  tradingRecordRegistry: TradingRecordRegistry;
  tradingModelRegistry: TradingModelRegistry;
}

interface Statistics {
  'algorithmic': TradingRecord;
  'q-learning': TradingRecord;
}

async function getStatistics(): Promise<Result<Statistics>> {
  const url = 'http://localhost:5000/stats';
  return fetch(url).then(response => {
    if (response.status !== 200) {
      const message = 'error retrieving statistics';
      console.error({ message, response, url });
      return new Error(message);
    }
    return response.json();
  });
}

// TODO: move long polling and rest of state management out of component
function longPollTradingInfo(this: App) {
  const interval = 500; // 0.5 seconds
  setTimeout(() => {
    getStatistics()
      .then((result: Result<Statistics>) => {
        if (result instanceof Error) {
          return;
        }
        const algorithmicTradingRecord = result['algorithmic'];
        const qLearningTradingRecord = result['q-learning'];
        this.props.tradingRecordRegistry.set('algorithmic', algorithmicTradingRecord);
        this.props.tradingRecordRegistry.set('q-learning', qLearningTradingRecord);
        this.forceUpdate();
      })
      .then(() => longPollTradingInfo.call(this));
  }, interval);
}

class App extends Component<AppProps, {}> {
  constructor(props: AppProps) {
    super(props);
  }

  componentDidMount() {
    longPollTradingInfo.call(this);
  }

  // TODO: create a statistics component containing TradingRecordView and TradesLineChart
  render() {
    return (
      <div className="App">
        <header className="App-header">
          <h1>
            HFT Client
          </h1>
        </header>
        <div className="App-statistics">
          <TradingRecordView tradingRecordRegistry={this.props.tradingRecordRegistry} tradingStrategy={'algorithmic'} />
          <TradesLineChart tradingRecordRegistry={this.props.tradingRecordRegistry} tradingStrategy={'algorithmic'} />
        </div>
        <div className="App-statistics">
          <TradingRecordView tradingRecordRegistry={this.props.tradingRecordRegistry} tradingStrategy={'q-learning'} />
          <TradesLineChart tradingRecordRegistry={this.props.tradingRecordRegistry} tradingStrategy={'q-learning'} />
        </div>
      </div>
    );
  }
}

export default App;
