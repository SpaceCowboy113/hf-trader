import { Maybe } from './maybe';

export type Result<T> = T | Error;

function withDefault<T>(defaultValue: T, result: Result<T>): T {
    return result instanceof Error ? defaultValue : result;
}

function andThen<T, V>(
    fn: (...args: T[]) => Result<V>,
    ...args: Result<T>[]
): Result<V> {
    if (args.every(value => !(value instanceof Error))) {
        return fn(...args as T[]);
    }
    return new Error('error found in argument');
}

// TODO: pipe function type signature can be improved by
// defining unique overloaded types manually for each
// number of functions piped.  This can ensure that the
// return value of one piped function matches the input
// argument of the next function.
type PipeFunction = (arg: any) => Result<any>;
const pipe = <RV>(...fns: PipeFunction[]) => (arg: any): Result<RV> => {
    const reducer = (result: Result<any>, fn: PipeFunction) => andThen(fn, result);
    return fns.reduce(reducer, arg);
}

function toMaybe<T>(result: Result<T>): Maybe<T> {
    return result instanceof Error ? undefined : result;
}

function fromMaybe<T>(maybe: Maybe<T>): Result<T> {
    if (maybe === null) {
        return new Error('maybe is null');
    }
    if (typeof maybe === 'undefined') {
        return new Error('maybe is undefined');
    }
    return maybe;
}

export const result = {
    withDefault,
    andThen,
    pipe,
    toMaybe,
    fromMaybe,
}
