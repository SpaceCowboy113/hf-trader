"""
Train neural network to predict Q value accurately
Choose the decision with the highest predicted Q value
Train neural network by keeping a table of records, actions, rewards, and next_records
Predict Q from records and Q' from next_records
Use formula to calculate Q(s, a) using reward, Q, Q', and GAMMA
Train Network
"""

import numpy as np
from typing import List, Any
from logger import logger
import random
import math
from pyrsistent import PRecord, field
from q_memory import QMemory, QMemorySample
import q_memory
from fully_connected_neural_network import FullyConnectedNeuralNetwork
import fully_connected_neural_network
from trading_record import TradingRecord, TradingAction
import tensorflow as tf
from q_records import QModelInput, QModelOutput

# Type aliases
# TODO: turn these into real types
History = Any
Tensor = Any
Model = Any
TensorFlowSession = Any


class QLearningModel(PRecord):
    memory = field(type=QMemory)
    neural_network = field(type=FullyConnectedNeuralNetwork)
    session = field(type=tf.Session)


def construct(session: TensorFlowSession) -> QLearningModel:
    return QLearningModel(
        memory=q_memory.construct(1000),
        neural_network=FullyConnectedNeuralNetwork(session),
        session=session
    )


def predict(q_model_input: QModelInput, model: QLearningModel) -> QModelOutput:
    input_tensor = translate_input_tensor(q_model_input)
    rewards_tensor = fully_connected_neural_network.predict_one(
        model.session,
        model.neural_network,
        input_tensor
    )
    return translate_output_tensor(rewards_tensor)


# Predict action using epsilon greedy algorithm to achieve approximate global minimum behavior
def predict_greedy_epsilon(
    q_model_input: QModelInput,
    model: QLearningModel,
    time_delta: int
) -> TradingAction:
    MIN_EPSILON = 0.1
    MAX_EPSILON = 0.75
    LAMBDA = 0.0001
    epsilon = MIN_EPSILON + (MAX_EPSILON - MIN_EPSILON) * math.exp(-LAMBDA * time_delta)
    print(epsilon)
    if random.random() < epsilon:
        randomPrediction = random.randint(0, 2)
        if randomPrediction is 0:
            return TradingAction(order='buy', amount=1)
        elif randomPrediction is 1:
            return TradingAction(order='sell', amount=1)
        else:
            return TradingAction(order='sell', amount=1)
    else:
        rewards = predict(q_model_input, model)
        return choose_best_action(rewards)


def translate_input_tensor(q_model_input: QModelInput) -> List[float]:
    exchange_rate = np.float64(q_model_input.exchange_rate)
    rate_of_change = np.float64(q_model_input.rate_of_change)
    moving_average = np.float64(q_model_input.moving_average)
    return np.array([exchange_rate, rate_of_change, moving_average])


def translate_output_tensor(rewards_tensor: List[List[float]]) -> QModelOutput:
    buy = np.float64(rewards_tensor[0][0])
    sell = np.float64(rewards_tensor[0][1])
    hold = np.float64(rewards_tensor[0][2])
    return QModelOutput(buy=buy, sell=sell, hold=hold)


def create_output_tensor(rewards: QModelOutput) -> List[float]:
    buy = np.float64(rewards['buy'])
    sell = np.float64(rewards['sell'])
    hold = np.float64(rewards['hold'])
    return np.array([buy, sell, hold])


def calculate_reward(pre_order_record: TradingRecord, post_order_record: TradingRecord):
    return post_order_record.usd - pre_order_record.usd


def choose_best_action(rewards: QModelOutput) -> TradingAction:
    maximum_order = max(rewards.iterkeys(), key=(lambda key: rewards[key]))
    return TradingAction(order=maximum_order, amount=1)


def train(model: QLearningModel) -> None:
    samples = q_memory.get_random_samples(10, model.memory)
    x_train = np.zeros((len(samples), 3))
    y_train = np.zeros((len(samples), 3))

    for index, sample in enumerate(samples):
        state = sample['neural_network_input']  # type: QModelInput
        action = sample['neural_network_prediction']  # type: TradingAction
        reward = sample['reward']  # type: float

        predicted_actions = predict(state, model)
        print(f'predicted_actions: {predicted_actions}')

        # If next state does not exist, do not calculate future reward
        if index + 1 >= len(samples):
            predicted_actions = predicted_actions.set(action.order, np.float64(reward))
        else:
            GAMMA = 0.15
            next_state = samples[index + 1]['neural_network_input']  # type: QModelInput
            predicted_future_actions = predict(next_state, model)

            q_delta_action = choose_best_action(predicted_future_actions)
            q_delta_reward = predicted_future_actions[q_delta_action.order]
            # Q(s, a) = r + GAMMA * Q(s', a')
            future_reward = reward + GAMMA * q_delta_reward
            predicted_actions = predicted_actions.set(action.order, np.float64(future_reward))

        x_train[index] = translate_input_tensor(state)
        y_train[index] = create_output_tensor(predicted_actions)

    fully_connected_neural_network.train_batch(
        model.session,
        model.neural_network,
        x_train,
        y_train
    )


def add_training_sample(
    neural_network_input: QModelInput,
    neural_network_prediction: TradingAction,
    reward: float,
    model: QLearningModel
) -> QLearningModel:
    q_memory_sample = QMemorySample(
        neural_network_input=neural_network_input,
        neural_network_prediction=neural_network_prediction,
        reward=reward
    )
    updatedMemory = q_memory.add(q_memory_sample, model.memory)
    return model.set('memory', updatedMemory)
