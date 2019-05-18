
import React, { Component } from 'react';
import { Line } from 'react-chartjs-2';
import { Maybe } from '../functional/maybe';
import { Order, TradingRecord, TradingRecordRegistry, Transaction, Subroutine, SubroutineResult } from '../state/trading-state';


function getPointBorderColor(order: Order): Maybe<string> {
    switch (order) {
        case 'buy':
            return 'rgb(151, 53, 53)';
        case 'sell':
            return 'rgb(46, 132, 46)';
    }
}

function getPointBackgroundColor(order: Order): Maybe<string> {
    switch (order) {
        case 'buy':
            return 'rgba(192,75,75,1)';
        case 'sell':
            return 'rgba(75,192,75,1)';
    }
}

function getSubroutineRGB(name: string): string {
    switch(name) {
        case 'moving_average_10':
            return '237,174,73';
        case 'moving_average_100':
            return '209,73,91';
        case 'little_moving_average':
            return '237,174,73';
        case 'big_moving_average':
            return '209,73,91';
        case 'filtered':
            return '95,75,182';
        default:
            // TODO: Randomly generate
            return '150,150,150';
    }
}

/**
 * Converts an epoch to a UTC timestamp
 * TODO: Detect time zone and convert timestamp accordingly.
 * (Probably should just use a library to do this)
 */
function getLabel(epoch: number): string {
    const date = new Date(0);
    date.setUTCSeconds(epoch);
    return date.toLocaleTimeString();
}

interface TradesLineChartProps {
    /**
     * TODO: instead give line chart reference to the object it needs to track
     * rather than registry+strategyKey for better decoupling.
     * (requires new state management tool like redux)
     */
    tradingRecordRegistry: TradingRecordRegistry;
    tradingStrategy: string;
}

interface TradesLineChartState {
    labels: string[];
    datasets: any[];
}

function getTransactions(transactionWindow: Transaction[]): Transaction[] {
    const xAxisMaxLength = 250;
    if (transactionWindow.length > xAxisMaxLength) {
        return transactionWindow.slice(transactionWindow.length - xAxisMaxLength);
    }
    return transactionWindow;
}

export default class TradesLineChart extends Component<TradesLineChartProps, TradesLineChartState> {
    options: any;

    constructor(props: TradesLineChartProps) {
        super(props);
        props.tradingRecordRegistry.onChange.add(({ key, value }) => {
            const tradingRecord = value;
            if (tradingRecord && key === this.props.tradingStrategy) {
                console.log(
                    `TradesLineChart.pushTradingRecord (${props.tradingStrategy})`,
                    tradingRecord,
                );
                this.pushTradingRecord(tradingRecord);
            }
        });

        this.options = {
            /**
             * In order for Chart.js to obey the custom size you
             * need to set maintainAspectRatio to false
             */
            maintainAspectRatio: false,
            legend: {
                display: true,
            }
        }
    }
    componentWillMount() {
        const initialState = {
            labels: [],
            datasets: [
                {
                    label: 'Exchange Rate',
                    fill: false,
                    lineTension: 0.1,
                    backgroundColor: 'rgba(75,192,192,0.8)',
                    borderColor: 'rgba(75,192,192,0.95)',
                    borderCapStyle: 'butt',
                    borderDash: [],
                    borderDashOffset: 0.0,
                    borderJoinStyle: 'miter',
                    pointBorderColor: 'rgba(75,192,192,1)',
                    pointBackgroundColor: '#fff',
                    pointBorderWidth: 1,
                    pointHoverRadius: 5,
                    pointHoverBackgroundColor: 'rgba(75,192,192,1)',
                    pointHoverBorderColor: 'rgba(220,220,220,1)',
                    pointHoverBorderWidth: 2,
                    pointRadius: 0,
                    pointHitRadius: 10,
                    steppedLine: true,
                    data: []
                },
                {
                    data: [],
                    label: 'Transactions',
                    fill: false,
                    backgroundColor: 'rgba(0,0,0,0)',
                    borderColor: 'rgba(0,0,0,0)',
                    pointBorderColor: [],
                    pointBackgroundColor: [],
                    pointBorderWidth: 1,
                    pointHoverRadius: [],
                    pointHoverBackgroundColor: 'rgba(75,192,192,1)',
                    pointHoverBorderColor: 'rgba(220,220,220,1)',
                    pointHoverBorderWidth: 2,
                    pointRadius: [],
                    pointHitRadius: []
                }
            ]
        };
        this.setState(initialState);
    }
    componentDidMount() {
    }

    pushTradingRecord(tradingRecord: TradingRecord) {
        // TODO: optimize by only graphing new data points rather than
        // entire transaction window on push
        const labels: string[] = [];
        const exchangeRates: number[] = [];
        const pointBorderColors: any[] = [];
        const pointBackgroundColors: any[] = [];
        const pointRadii: any[] = [];
        const pointHitRadii: any[] = [];
        const pointHoverRadii: any[] = [];

        tradingRecord.exchange_rates.samples.forEach((sample, index) => {
            const exchangeRate = sample.exchange_rate;

            exchangeRates.push(exchangeRate);
        });
        const exchangeRateLine = this.state.datasets[0];
        exchangeRateLine.data = exchangeRates;

        getTransactions(tradingRecord.transaction_window).forEach((transaction, index) => {
            const pointBorderColor = getPointBorderColor(transaction.order);
            const pointBackgroundColor = getPointBackgroundColor(transaction.order);
            const pointRadius = Math.max(transaction.quantity * 5, 5);
            const pointHitRadius = pointRadius;
            const pointHoverRadius = pointRadius / 2;

            pointBorderColors.push(pointBorderColor);
            pointBackgroundColors.push(pointBackgroundColor);
            pointRadii.push(pointRadius);
            pointHitRadii.push(pointHitRadius);
            pointHoverRadii.push(pointHoverRadius);
            labels.push(getLabel(transaction.epoch));
        });
        const pointLine = this.state.datasets[1];
        pointLine.data = exchangeRates;
        pointLine.pointBorderColor = pointBorderColors;
        pointLine.pointBackgroundColor = pointBackgroundColors;
        pointLine.pointRadius = pointRadii;
        pointLine.pointHoverRadius = pointHoverRadii;
        pointLine.pointHitRadius = pointHitRadii;

        const datasets = [exchangeRateLine, pointLine];

        // Push a line for each subroutine executing in the trading record
        Object.keys(tradingRecord.exchange_rates.subroutines).forEach((name, index) => {
            const subroutine = tradingRecord.exchange_rates.subroutines[name];
            if (subroutine != null) {
                const values: number[] = [];

                subroutine.results.forEach((result, index) => {
                    if ('value' in result.data) {
                        values.push(result.data.value);
                    } else {
                        values.push(0);
                        console.log(`Error: ${result} doesn't contain a value to plot.`)
                    }
                });
    
                const rgb = getSubroutineRGB(name);
                const subroutineLine = {
                    'label': name,
                    'data': values,
                    'backgroundColor': `rgb(${rgb}, 0.8)`,
                    'borderColor': `rgb(${rgb}, 0.95)`,
                    'pointBorderColor': `rgb(${rgb}, 1)`,
                    'pointHoverBackgroundColor': `rgb(${rgb}, 1)`,
                    'fill': false,
                    'lineTension': 0.1,
                    'borderCapStyle': 'butt',
                    'borderDash': [],
                    'borderDashOffset': 0.0,
                    'borderJoinStyle': 'miter',
                    'pointBackgroundColor': '#fff',
                    'pointBorderWidth': 1,
                    'pointHoverRadius': 5,
                    'pointHoverBorderColor': 'rgba(220,220,220,1)',
                    'pointHoverBorderWidth': 2,
                    'pointRadius': 0,
                    'pointHitRadius': 10,
                    'steppedLine': true
                }
                datasets.push(subroutineLine);
            }
        });

        this.setState({
            labels,
            datasets,
        });
    }
    render() {
        return (
            <div className='App-line-chart'>
                <Line data={this.state} options={this.options} />
            </div>
        );
    }
}
