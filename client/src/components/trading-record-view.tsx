import React, { PureComponent } from 'react';
import {
    TradingRecordRegistry,
    calculateNetWorth,
    calculateProfit,
    TradingStrategy,
} from '../state/trading-state';
import { maybe } from '../functional/maybe';

interface TradingRecordProps {
    tradingRecordRegistry: TradingRecordRegistry;
    tradingStrategy: TradingStrategy;
}

function displayNetWorth(props: TradingRecordProps): string {
    const tradingRecord = props.tradingRecordRegistry.get(props.tradingStrategy);
    return tradingRecord
        ? String(calculateNetWorth(tradingRecord).toFixed(2))
        : 'unknown';
}

function displayProfit(props: TradingRecordProps): string {
    const tradingRecord = props.tradingRecordRegistry.get(props.tradingStrategy);
    return tradingRecord
        ? String(calculateProfit(tradingRecord).toFixed(2))
        : 'unknown';
}

function displayTradingRecordProperty(
    props: TradingRecordProps,
    propertyKey: string,
): string {
    const tradingRecord = props.tradingRecordRegistry.get(props.tradingStrategy);
    const property = maybe.pipe<string>(
        tradingRecord => tradingRecord[propertyKey],
        property => Number.parseFloat(property).toFixed(2),
        property => String(property),
    )(tradingRecord);
    return maybe.withDefault('unknown', property);

    // The above is equivalent to...
    // if (tradingRecord) {
    //     const property = tradingRecord[propertyKey];
    //     if (property !== undefined) {
    //         const fixedFloatingPoint = Number.parseFloat(property).toFixed(2)
    //         return String(fixedFloatingPoint);
    //     }
    // }
    // return 'unknown';
}

function displayLength(maybeArray: any[] | string): string {
    if (Array.isArray(maybeArray)) {
        return String(maybeArray.length);
    }
    return 'none';
}

function capitalizeWord(word: string): string {
    return word.charAt(0).toUpperCase() + word.slice(1);
}

export default class TradingRecordView extends PureComponent<TradingRecordProps> {
    constructor(props: TradingRecordProps) {
        super(props);
        props.tradingRecordRegistry.onChange.add(({ key, value }) => {
            const tradingRecord = value;
            if (tradingRecord && key === this.props.tradingStrategy) {
                this.forceUpdate();
            }
        });
    }

    render() {
        return (
            <div className="App-trading-record-view">
                <div className="App-trading-record-view-title">{capitalizeWord(this.props.tradingStrategy)}</div>
                <div>Net Worth: {displayNetWorth(this.props)}</div>
                <div>Profit: {displayProfit(this.props)}</div>
                <div>USD: {displayTradingRecordProperty(this.props, 'usd')}</div>
                <div>Bitcoin: {displayTradingRecordProperty(this.props, 'crypto')}</div>
                <div>Fees Paid: {displayTradingRecordProperty(this.props, 'fees_paid')}</div>
                <div>Buys: {displayTradingRecordProperty(this.props, 'buys')}</div>
                <div>Sells: {displayTradingRecordProperty(this.props, 'sells')}</div>
                <div>Holds: {displayTradingRecordProperty(this.props, 'holds')}</div>
                <div>Pending Sales: {
                    displayLength(
                        displayTradingRecordProperty(this.props, 'pending_sales')
                    )
                }
                </div>
                <div>Total Transactions: {
                    displayLength(
                        displayTradingRecordProperty(this.props, 'transaction_window')
                    )
                }
                </div>
                {/* <p>{displayTradingRecordProperty(this.props, 'description')}</p> */}
            </div>
        );
    }
}
