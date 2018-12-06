from random import randrange
import time
from eth_utils import (
    big_endian_to_int,
)
from plasmalib.state import get_total_deposits_key, State
from plasmalib.utils import (
    int_to_big_endian8,
)


def test_deposit(blank_state, mock_accts):
    state = blank_state
    for a in mock_accts:
        state.add_deposit(a.address, 0, 10)
    # Check that total deposits was incremented correctly
    end_total_deposits = big_endian_to_int(state.db.get(get_total_deposits_key(int_to_big_endian8(0))))
    assert end_total_deposits == 1000
    print('End total deposits:', end_total_deposits)


def test_get_ranges(blank_state, mock_accts):
    state = blank_state
    for i in range(10):
        state.add_deposit(mock_accts[0].address, 0, 10)


def test_performace_get_ranges(blank_state, mock_accts):
    state = blank_state
    total_deposits = 1000000
    start_time = time.time()
    # Deposit a bunch of tokens
    for i in range(total_deposits//10000):
        for a in mock_accts:
            # This will run 10000 deposits because there are 100 accts & each deposits 10 times
            for i in range(10):
                state.add_deposit(a.address, 0, 10)
    added_deposits_time = time.time()
    # Select a bunch of ranges
    for i in range(100000):
        dist_from_middle = randrange(1, 500)
        middle_select = randrange(dist_from_middle, total_deposits-dist_from_middle)
        state.get_ranges(0, middle_select - dist_from_middle, middle_select + dist_from_middle)
    get_ranges_time = time.time()

    print('~~~~~~~~~~~~~~ RESULTS ~~~~~~~~~~~~~~')
    print('Deposit time:', added_deposits_time - start_time)
    print('Get ranges time:', get_ranges_time - added_deposits_time)


def test_large_state_get_ranges():
    db_path = '/tmp/plasma_prime_blank_test_db/1543988143.476207'
    file_log_path = '/tmp/plasma_prime_blank_test_tx_log/1543988143.476207'
    state = State(db_path, file_log_path, backup_timeout=60)
    total_deposits = 100000000
    start_time = time.time()
    for i in range(100000):
        dist_from_middle = randrange(1, 500)
        middle_select = randrange(dist_from_middle, total_deposits-dist_from_middle)
        state.get_ranges(0, middle_select - dist_from_middle, middle_select + dist_from_middle)
    get_ranges_time = time.time()
    print('Get ranges time:', get_ranges_time - start_time)
