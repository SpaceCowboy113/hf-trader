def create_stub(returns=None):
    def stub(*args):
        stub.called += 1
        stub.called_with.append(args)
        return returns

    stub.called = 0
    stub.called_with = []
    return stub
