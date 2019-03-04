import ObservableMap from './observable-map';
import { Maybe } from './maybe';
// import * as maybe from './maybe';

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