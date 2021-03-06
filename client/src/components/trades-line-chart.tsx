
import React, { Component } from 'react';
import { Line } from 'react-chartjs-2';
import { Maybe } from '../functional/maybe';
import { Order, TradingRecord, TradingRecordRegistry, Transaction } from '../state/trading-state';


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
                    label: "Exchange Rate",
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
                    label: "Transactions",
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
                },
                {
                    label: "Filtered",
                    fill: false,
                    lineTension: 0.1,
                    backgroundColor: 'rgba(95,75,182,0.8)',
                    borderColor: 'rgba(95,75,182,0.95)',
                    borderCapStyle: 'butt',
                    borderDash: [],
                    borderDashOffset: 0.0,
                    borderJoinStyle: 'miter',
                    pointBorderColor: 'rgba(95,75,182,1)',
                    pointBackgroundColor: '#fff',
                    pointBorderWidth: 1,
                    pointHoverRadius: 5,
                    pointHoverBackgroundColor: 'rgba(95,75,182,1)',
                    pointHoverBorderColor: 'rgba(220,220,220,1)',
                    pointHoverBorderWidth: 2,
                    pointRadius: 0,
                    pointHitRadius: 10,
                    steppedLine: true,
                    data: []
                },
                {
                    label: "Moving Average (10)",
                    fill: false,
                    lineTension: 0.1,
                    backgroundColor: 'rgba(237,174,73,0.8)',
                    borderColor: 'rgba(237,174,73,0.95)',
                    borderCapStyle: 'butt',
                    borderDash: [],
                    borderDashOffset: 0.0,
                    borderJoinStyle: 'miter',
                    pointBorderColor: 'rgba(237,174,73,1)',
                    pointBackgroundColor: '#fff',
                    pointBorderWidth: 1,
                    pointHoverRadius: 5,
                    pointHoverBackgroundColor: 'rgba(237,174,73,1)',
                    pointHoverBorderColor: 'rgba(220,220,220,1)',
                    pointHoverBorderWidth: 2,
                    pointRadius: 0,
                    pointHitRadius: 10,
                    steppedLine: true,
                    data: []
                },
                {
                    label: "Moving Average (100)",
                    fill: false,
                    lineTension: 0.1,
                    backgroundColor: 'rgba(209,73,91,0.8)',
                    borderColor: 'rgba(209,73,91,0.95)',
                    borderCapStyle: 'butt',
                    borderDash: [],
                    borderDashOffset: 0.0,
                    borderJoinStyle: 'miter',
                    pointBorderColor: 'rgba(209,73,91,1)',
                    pointBackgroundColor: '#fff',
                    pointBorderWidth: 1,
                    pointHoverRadius: 5,
                    pointHoverBackgroundColor: 'rgba(209,73,91,1)',
                    pointHoverBorderColor: 'rgba(220,220,220,1)',
                    pointHoverBorderWidth: 2,
                    pointRadius: 0,
                    pointHitRadius: 10,
                    steppedLine: true,
                    data: []
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
        const exchangeRatesFiltered: number[] = [];
        const exchangeRateMovingAverages10: number[] = [];
        const exchangeRateMovingAverages100: number[] = [];
        const pointExchangeRates: any[] = [];
        const pointBorderColors: any[] = [];
        const pointBackgroundColors: any[] = [];
        const pointRadii: any[] = [];
        const pointHitRadii: any[] = [];
        const pointHoverRadii: any[] = [];

        tradingRecord.exchange_rates.samples.forEach((sample, index) => {
            const exchangeRate = sample.exchange_rate;
            const exchangeRateFiltered = sample.exchange_rate_filtered;
            const exchangeRateMovingAverage10 = sample.exchange_rate_moving_average_10
            const exchangeRateMovingAverage100 = sample.exchange_rate_moving_average_100

            exchangeRates.push(exchangeRate);
            exchangeRatesFiltered.push(exchangeRateFiltered);
            exchangeRateMovingAverages10.push(exchangeRateMovingAverage10)
            exchangeRateMovingAverages100.push(exchangeRateMovingAverage100)
        });
        const exchangeRateLine = this.state.datasets[0];
        exchangeRateLine.data = exchangeRates;
        const exchangeRateFilteredLine = this.state.datasets[2];
        exchangeRateFilteredLine.data = exchangeRatesFiltered;
        const exchangeRateMovingAverage10Line = this.state.datasets[3];
        exchangeRateMovingAverage10Line.data = exchangeRateMovingAverages10;
        const exchangeRateMovingAverage100Line = this.state.datasets[4];
        exchangeRateMovingAverage100Line.data = exchangeRateMovingAverages100;

        getTransactions(tradingRecord.transaction_window).forEach((transaction, index) => {
            const pointBorderColor = getPointBorderColor(transaction.order);
            const pointBackgroundColor = getPointBackgroundColor(transaction.order);
            const pointRadius = transaction.quantity * 5;
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

        const datasets = [exchangeRateLine, pointLine, exchangeRateFilteredLine,
            exchangeRateMovingAverage10Line, exchangeRateMovingAverage100Line];

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
