export type Maybe<T> = T | void;

function withDefault<T>(defaultValue: T, maybe: Maybe<T>): T {
    return exists(maybe) ? maybe as T : defaultValue;
}

function andThen<T, V>(
    fn: (...args: T[]) => Maybe<V>,
    ...args: Maybe<T>[]
): Maybe<V> {
    if (args.every(value => exists(value))) {
        return fn(...args as T[]);
    }
}

// TODO: pipe function type signature can be improved by
// defining unique overloaded types manually for each
// number of functions piped.  This can ensure that the
// return value of one piped function matches the input
// argument of the next function.
type PipeFunction = (arg: any) => Maybe<any>;
const pipe = <RV>(...fns: PipeFunction[]) => (arg: any): Maybe<RV> => {
    const reducer = (result: Maybe<any>, fn: PipeFunction) => andThen(fn, result);
    return fns.reduce(reducer, arg);
}

function exists<T>(maybe: Maybe<T>): boolean {
    if (maybe !== null && typeof maybe !== 'undefined') {
        return true;
    }
    return false;
}

export const maybe = {
    withDefault,
    andThen,
    pipe,
    exists,
}
