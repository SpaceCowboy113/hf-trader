# High-Frequency Crypto Trader

A program that looks at minor exchange rate fluctuations to make crypto currency trading decisions. Crypto currencies have lower trading fees and looser regulations than traditional assets like stocks, making them a solid asset choice when it comes to daytrading. The goal of this project is to use high-frequency trading as a means of learning more about machine learning. The project currently runs as a simulation that pulls real-time crypto currency exchange rates from coinbase pro to make buy/sell trading decisions. Once a decision has been made by the trading algorithm, the program simulates the execution of the order without posting it to coinbase pro. Once an order is simulated, profit/loss are calculated in a simulated wallet.

This project contains a server and client. The backend, written in python 3, is the bread and butter of the program. It makes all of the trading decisions. The client, written in Typescript+React.js, provides data visualization and real-time statistics that aid in algorithm development. Although Python has its pitfalls, Python was chosen in tandem with Google's popular machine learning library, Tensorflow. Although Tensorflow supports other languages, those languages lack features (like tensorboard) found in the Tensorflow Python distribution and as a consequence, feel like second-class citizens.

## Installation

- Requirements:

  - [python v3.7](https://www.python.org/downloads/)
  - [pipenv](https://pipenv.readthedocs.io/en/latest/)
  - [node.js](https://nodejs.org/en/)
  - [npm](https://www.npmjs.com/get-npm)

## Development

### Server

The server uses **pipenv** to manage python dependencies. **pipenv** is a tool that uses **pip** to install/manage dependencies and **virtualenv** to enable virtual environments. **pipenv** records the project's python dependencies in a Pipfile. The Pipfile is analogous to **npm's** package.json file. In the server directory run **pipenv install** to install the python dependencies found in the Pipfile. Pipfile. With the dependencies installed run **pipenv shell** to enable the virtual environment. This gives the project access to all of the dependencies that were installed with **pipenv install**. Because the web client uses **npm** to manage project scripts in a package.json file, the server does as well to maintain a symmetrical workflow. Once your virtual environment is enabled, run **npm start** to launch the server. **npm start** runs the following (found in server/package.json):

_mypy --config-file mypy.ini src/main.py && python3 src/main.py_

**mypy** is a tool that performs static type checking on the type hints found in python server code. The server can be ran without checking the static types by running _python3 src/main.py_; however, this isn't advised. Although this project does not currently run any testing and validation against git commits, all checked in code should pass **mypy's** static analysis.

**IMPORTANT**: When installing a new external python library, make sure the library's types are installed or ignored. Skipping this step will cause _mypy's_ static analysis to fail. Library types can be ignored in the mypy.ini.

### Client

The client is just a standard web project and as a consequence, requires **node.js** and the **node.js** package manager, or **npm** for short. The client dependencies are found in the **package.json** and can be installed by running **npm install** in the client directory. The client uses Typescript+React to build a user interface for data visualization and was bootstrapped using the react-create-app tool. react-create-app handles our build and testing configuration so that we can focus on just building our user interface and not have to worry about things like building/testing configurations. After installing project dependencies with **npm install**, the client can be launched in a development mode by running **npm start** in navigating to **<http://localhost:3000/>** in your web browser. To just build the project run **npm build** and to test the project with Jest, run **npm start**. The scripts being executed by these commands can be found in the client's **package.json** under the "scripts" key.

## Testing

### Server

Unit tests use **pytest** and can be ran by running the command **npm test** in the server folder. Unit test files can be found alongside the files being tested with a _test__ prefix in the name. For example, the unit tests for sliding_window.py can be found inside the same folder containing sliding_window.py within test_sliding_window.py.

### Client

Unit tests use **Jest** and can be ran by running the command **npm test** in the client folder. Like the server, unit test files can be found alongside the corresponding files in test. Unit testing files on the client have a **.test.*** extension. (ie. .test.tsx to test a React component).
