export type Maybe<T> = T | void;

/**
 * TODO: consider removing these util functions a using just the Maybe
 * type alias
 */
function exists<T>(maybe: Maybe<T>): boolean {
    if(maybe !== null && typeof maybe !== 'undefined') {
        return true;
    }
    return false;
}

function withDefault<T>(defaultValue: T, maybe: Maybe<T>): T {
    return exists(maybe) ? maybe as T : defaultValue;
}

function andThen<T, V>(
    fn: (...args: T[]) => Maybe<V>,
    ...args: Maybe<T>[]
): Maybe<V> {
    if (args.every(value => value !== undefined)) {
        return fn(...args as T[]);
    }
}

function map<T, V>(callback: (value: T) => V, maybe: Maybe<T>): Maybe<V> {
    if (exists(maybe)) {
        return callback(maybe as T);
    }
}

function map2<T, V>(
    callback: (a: T, b: T) => V,
    maybe1: Maybe<T>,
    maybe2: Maybe<T>,
): Maybe<V> {
    if (exists(maybe1) && exists(maybe2)) {
        return callback(maybe1 as T, maybe2 as T);
    }
}

export const maybe = {
    exists,
    withDefault,
    andThen,
}