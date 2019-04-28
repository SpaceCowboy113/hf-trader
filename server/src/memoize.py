from pyrsistent import PRecord, field, pvector_field


def memoize(f):  # Memoize a given function f
    def memf(*x):
        if x not in memf.cache:
            print('calling function', x)
            memf.cache[x] = f(*x)
            return memf.cache[x]
        print('returning cached results', x)
        return memf.cache[x]

    memf.cache = {}
    return memf


class Character(PRecord):
    name = field(type=str, mandatory=True)
    power = field(type=int, mandatory=True)


henry = Character(
    name='henry',
    power=10,
)

jeff = Character(
    name='jeff',
    power=15,
)

@memoize
def fight(x: Character, y: Character) -> Character:
    print('executing fight', x, y)
    if x.power > y.power:
        return x
    else:
        return y


# mfight = memoize(fight)

winner = fight(henry, jeff)
winner2 = fight(henry, jeff)
henry_copy = henry
winner3 = fight(henry_copy, jeff)

print('Winner: ', winner.name)
print('Winner2: ', winner2.name)
print('Winner3 (when called with copy): ', winner3.name)