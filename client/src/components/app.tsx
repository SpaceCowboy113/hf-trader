import React, { Component } from 'react';
import '../style/app.css';
import TradesLineChart from './trades-line-chart';
import {
    TradingRecordRegistry,
    TradingModelRegistry,
    longPollTradingInfo,
} from '../state/trading-state';
import TradingRecordView from './trading-record-view';

interface AppProps {
    tradingRecordRegistry: TradingRecordRegistry;
    tradingModelRegistry: TradingModelRegistry;
}

class App extends Component<AppProps, {}> {
    constructor(props: AppProps) {
        super(props);
    }

    componentDidMount() {
        longPollTradingInfo(
            this.props.tradingRecordRegistry,
            this.props.tradingModelRegistry,
        );
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
