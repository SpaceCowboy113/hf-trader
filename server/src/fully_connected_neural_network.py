import tensorflow as tf


# TODO: refactor to use tensorflow estimator API instead
class FullyConnectedNeuralNetwork:
    def __init__(self, session, input_size, output_size, batch_size):
        self.input_size = input_size
        self.output_size = output_size
        self.batch_size = batch_size

        self.input = None
        self.output = None

        self.output_operation = None

        self.optimizer = None
        self.variable_initializer = None

        self.input = tf.placeholder(shape=[None, self.input_size], dtype=tf.float64)
        self.output = tf.placeholder(shape=[None, self.output_size], dtype=tf.float64)

        layer_one = tf.layers.dense(self.input, 50, activation=tf.nn.relu)
        layer_two = tf.layers.dense(layer_one, 50, activation=tf.nn.relu)

        self.output_operation = tf.layers.dense(layer_two, self.output_size)
        loss = tf.losses.mean_squared_error(self.output, self.output_operation)
        self.optimizer = tf.train.AdamOptimizer().minimize(loss)

        variable_initializer = tf.global_variables_initializer()
        session.run(variable_initializer)


def predict_one(session, neural_network, input):
    feed_dict = {
        neural_network.input: input.reshape(1, neural_network.input_size)
    }
    return session.run(neural_network.output_operation, feed_dict=feed_dict)


def predict_batch(session, neural_network, input):
    feed_dict = {
        neural_network.input: input
    }
    return session.run(neural_network.output_operation, feed_dict=feed_dict)


def train_batch(session, neural_network, x_batch, y_batch):
    feed_dict = {
        neural_network.input: x_batch,
        neural_network.output: y_batch
    }
    session.run(neural_network.optimizer, feed_dict=feed_dict)
    # Because this server is not using asynchronous event
    # loop, the server is unable to do anything else when
    # training occurs.
    # TODO: Implement asynchronous event loop using asyncio and
    # verify by checking that coinbase messages can still be received
    # while training and sleeping for 30 seconds
    # for i in range(0, 30):
    #     print(f'sleeping... {i}')
    #     time.sleep(1)
