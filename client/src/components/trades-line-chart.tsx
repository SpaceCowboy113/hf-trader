
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

// TODO: create a more robust way of formatting timestamp
//       by converting to time object
function getLabel(timestamp: string): string {
    return timestamp.slice(14, timestamp.length - 4);
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
                display: false,
            }
        }
    }
    componentWillMount() {
        const initialState = {
            labels: [],
            datasets: [
                {
                    label: null,
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
                    data: []
                },
                {
                    data: [],
                    pointBorderColor: [],
                    pointBackgroundColor: [],
                    pointBorderWidth: 1,
                    pointHoverRadius: [],
                    pointHoverBackgroundColor: 'rgba(75,192,192,1)',
                    pointHoverBorderColor: 'rgba(220,220,220,1)',
                    pointHoverBorderWidth: 2,
                    pointRadius: [],
                    pointHitRadius: [],
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
        const pointExchangeRates: any[] = [];
        const pointBorderColors: any[] = [];
        const pointBackgroundColors: any[] = [];
        const pointRadii: any[] = [];
        const pointHitRadii: any[] = [];
        const pointHoverRadii: any[] = [];

        getTransactions(tradingRecord.transaction_window).forEach((transaction, index) => {
            const exchangeRate = transaction.exchange_rate;
            const pointBorderColor = getPointBorderColor(transaction.order);
            const pointBackgroundColor = getPointBackgroundColor(transaction.order);
            const pointRadius = transaction.quantity * 5;
            const pointHitRadius = pointRadius;
            const pointHoverRadius = pointRadius / 2;

            exchangeRates.push(exchangeRate);
            pointExchangeRates.push(exchangeRate);
            pointBorderColors.push(pointBorderColor);
            pointBackgroundColors.push(pointBackgroundColor);
            pointRadii.push(pointRadius);
            pointHitRadii.push(pointHitRadius);
            pointHoverRadii.push(pointHoverRadius);
            labels.push(getLabel(transaction.timestamp));
        });
        const exchangeRateLine = this.state.datasets[0];
        exchangeRateLine.data = exchangeRates;
        const pointLine = this.state.datasets[1];
        pointLine.data = exchangeRates;
        pointLine.pointBorderColor = pointBorderColors;
        pointLine.pointBackgroundColor = pointBackgroundColors;
        pointLine.pointRadius = pointRadii;
        pointLine.pointHoverRadius = pointHoverRadii;
        pointLine.pointHitRadius = pointHitRadii;

        const datasets = [exchangeRateLine, pointLine];

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