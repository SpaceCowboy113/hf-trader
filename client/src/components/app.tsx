import React, { PureComponent } from 'react';
import '../style/app.css';
import TradesLineChart from './trades-line-chart';
import {
    TradingRecordRegistry,
    TradingModelRegistry,
    longPollTradingInfo,
    TradingStrategy,
} from '../state/trading-state';
import TradingRecordView from './trading-record-view';

interface StatisticsProps {
    tradingRecordRegistry: TradingRecordRegistry;
    tradingStrategy: TradingStrategy;
}

function Statistics(props: StatisticsProps) {
    return (
        <div className="App-statistics">
            <TradingRecordView
                tradingRecordRegistry={props.tradingRecordRegistry}
                tradingStrategy={props.tradingStrategy}
            />
            <TradesLineChart
                tradingRecordRegistry={props.tradingRecordRegistry}
                tradingStrategy={props.tradingStrategy}
            />
        </div>
    );
}

interface AppProps {
    tradingRecordRegistry: TradingRecordRegistry;
    tradingModelRegistry: TradingModelRegistry;
}

class App extends PureComponent<AppProps> {
    constructor(props: AppProps) {
        super(props);
    }

    componentDidMount() {
        longPollTradingInfo(
            this.props.tradingRecordRegistry,
            this.props.tradingModelRegistry,
        );
    }

    render() {
        return (
            <div className="App">
                <header className="App-header">
                    <h1>
                        HFT Client
                    </h1>
                </header>
                <Statistics
                    tradingRecordRegistry={this.props.tradingRecordRegistry}
                    tradingStrategy={'algorithmic'}
                />
                <Statistics
                    tradingRecordRegistry={this.props.tradingRecordRegistry}
                    tradingStrategy={'q-learning'}
                />

            </div>
        );
    }
}

export default App;
