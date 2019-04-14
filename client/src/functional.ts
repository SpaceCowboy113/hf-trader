
import { Maybe, maybe } from './maybe';


type PipeFunction = (arg: any) => Maybe<any>;
export const pipe = (...fns: PipeFunction[]) => (arg: any) => {
    // procedural implementation
    // let result = arg;
    // for(let i = 0;i < fns.length;i++) {
    //   if (result !== undefined) {
    //     result = fns[i](result);  
    //   }
    // }
    // return result;


    // functional implementation
    const reducer = (result: Maybe<any>, fn: PipeFunction) => maybe.andThen(fn, result);
    return fns.reduce(reducer, arg);
}