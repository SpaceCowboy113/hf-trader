import { Signal } from 'micro-signals';
import { string } from 'prop-types';
import { Maybe } from './maybe';

interface OnChangePayload<T> {
    key: string;
    value?: T;
}

export default class ObservableMap<T> {
    private _map: Map<string, Maybe<T>>;
    onChange: Signal<OnChangePayload<T>>;

    constructor() {
        // TODO: look into shorthand
        this._map = new Map<string, Maybe<T>>();
        this.onChange = new Signal();
    }

    set(key: string, value: T): ObservableMap<T> {
        this._map.set(key, value);
        this.onChange.dispatch({ key, value });
        return this;
    }

    get(key: string): Maybe<T> {
        return this._map.get(key);
    }

    has(key: string): boolean {
        return this._map.has(key);
    }

    remove(key: string): ObservableMap<T> {
        this._map.delete(key);
        this.onChange.dispatch({ key, value: undefined });
        return this;
    }
}
