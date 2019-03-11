# General Purpose Plasma Python Implementation
This repository contains code which simulates a 'generalized plasma' implementation. This means that
it implements a few smart contracts which share a common interface that allow for maximal layer 2 interoperability.

This repository contains a standard plasma chain, but also includes python implementations of common state channels like
payment channels. It also contains more sophisticated plasma `predicate` logic which handles things like multi-sigs & more.

Note that this was written in Python so that it can serve as an easy to digest example of these topics. A more special purpose
language would be used in practice, like Vyper. However, the core logic will remain the same even if there are slight data structure
changes & things like signatures and inclusion proofs will not be mocked.

## Requirements
- Python3

## Installation
```
$ cd gen-plasma # navigate to root directory
$ python3 -m venv venv # create virtual enviornment
$ . venv/bin/activate # activate virtual enviornment
$ pip install pytest # install pytest--the only dependency
```

## Test it out
```
$ pytest # run the tests!

test/test_erc20_plasma_contract.py ..
test/test_utils.py .                 
test/predicates/test_multisig.py ....
test/predicates/test_transfer.py ....

========== x passed in 0.06 seconds ==========
$ # You did it! Now take a look at the code :)
$ vim test/predicates/test_transfer.py # the transfer predicate is a pretty good place to start :)
```
