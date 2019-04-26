import ObservableMap from './observable-map';
import { Maybe } from '../functional/maybe';
import { Result } from '../functional/result';

export interface AlgorithmicModel {

}

export interface QLearningModel {

}

export type TradingModel = AlgorithmicModel | QLearningModel;

export type Order = 'buy' | 'sell' | 'hold';

export interface Transaction {
    label: string;
    quantity: number;
    exchange_rate: number;
    timestamp: string;
    fees: number;
    order: Order;
}

// TODO: rename this to ExchangeRateSample
export interface SlidingWindowSample {
    exchange_rate: number;
    filtered_exchange_rate: number;
    epoch: number;
}

// TODO: rename this to ExchangeRateWindow
export interface SlidingWindow {
    samples: SlidingWindowSample[];
    maximum_size: number;
}

export interface TradingRecord {
    name: string;
    description: string;
    initial_usd: number;
    usd: number;
    crypto: number;
    buys: number;
    sells: number;
    holds: number;
    exchange_rates: any;
    fees_paid: number;
    pending_sales: any[];
    transaction_window: Transaction[];
}

export type TradingRecordRegistry = ObservableMap<TradingRecord>;

export type TradingModelRegistry = ObservableMap<TradingModel>;

export function getExchangeRate(tradingRecord: TradingRecord): Maybe<number> {
    const samples = tradingRecord.exchange_rates.samples;
    if (samples.length > 0) {
        const latestSample = samples[samples.length - 1];
        return latestSample.exchange_rate;
    }
}

export function calculateNetWorth(tradingRecord: TradingRecord): number {
    const exchangeRate = getExchangeRate(tradingRecord);
    if (exchangeRate !== undefined) {
        return tradingRecord.usd + tradingRecord.crypto * exchangeRate;
    }
    return tradingRecord.usd;
}

export function calculateProfit(tradingRecord: TradingRecord): number {
    const netWorth = calculateNetWorth(tradingRecord);
    return netWorth - tradingRecord.initial_usd;
}

export interface Statistics {
    'algorithmic': TradingRecord;
    'q-learning': TradingRecord;
}

export type TradingStrategy = keyof Statistics;

export function longPollTradingInfo(
    tradingRecordRegistry: TradingRecordRegistry,
    tradingModelRegistry: TradingModelRegistry,
) {
    const interval = 500; // 0.5 seconds
    const getStatistics = () => {
        const url = 'http://localhost:5000/stats';
        const response = fetch(url).then(response => {
            if (response.status !== 200) {
                const message = 'error retrieving statistics';
                console.error({ message, response, url });
                return new Error(message);
            }
            return response.json();
        }).then((result: Result<Statistics>) => {
            if (result instanceof Error) {
                return;
            }
            const algorithmicTradingRecord = result['algorithmic'];
            const qLearningTradingRecord = result['q-learning'];
            tradingRecordRegistry.set(
                'algorithmic',
                algorithmicTradingRecord,
            );
            tradingRecordRegistry.set(
                'q-learning',
                qLearningTradingRecord,
            );

            // TODO: pull trading models from server and set here
            tradingModelRegistry.set('algorithmic', {});
            tradingModelRegistry.set('q-learning', {});
        }).then(() => longPollTradingInfo(
            tradingRecordRegistry,
            tradingModelRegistry,
        ));
    }
    setTimeout(getStatistics, interval);
}
