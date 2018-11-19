def subtract_range(range_list, start, end):
    affected_range = None
    for i in range(0, len(range_list), 2):
        r_start = range_list[i]
        r_end = range_list[i+1]
        if r_start <= start and end <= r_end:
            affected_range = i
            break
    assert affected_range is not None
    # Remove the effected range
    del range_list[i:i + 2]
    # Create new sub-ranges based on what we deleted
    if r_start < start:
        range_list += [r_start, start - 1]
    if r_end > end:
        range_list += [end + 1, r_end]


def add_range(range_list, start, end):
    # Find left_range (a range which ends at the start of our tx) and right_range (a range which starts at the end of our tx)
    left_range = None
    right_range = None
    for i in range(0, len(range_list), 2):
        if range_list[i+1] == start - 1:
            left_range = i
        if range_list[i] == end + 1:
            right_range = i
    # Set the start and end of our new range based on the deleted ranges
    if left_range is not None:
        start = range_list[left_range]
    if right_range is not None:
        end = range_list[right_range + 1]
    # Delete the left_range and right_range if we found them
    if left_range is not None and right_range is not None:
        # Delete them in such a way that the first delete does not effect the index of the second delete
        if left_range > right_range:
            del range_list[left_range:left_range + 2]
            del range_list[right_range:right_range + 2]
        else:
            del range_list[right_range:right_range + 2]
            del range_list[left_range:left_range + 2]
    elif left_range is not None:
        del range_list[left_range:left_range + 2]
    elif right_range is not None:
        del range_list[right_range:right_range + 2]
    range_list += [start, end]


def add_tx(db, tx):
    # Now make sure the range is owned by the sender
    sender_ranges = db.get(tx.sender)
    tx_start = tx.start
    tx_end = tx.start + tx.offset - 1
    # Subtract ranges from sender range list and store
    subtract_range(sender_ranges, tx_start, tx_end)
    db.put(tx.sender, sender_ranges)
    # After having deleted the sender ranges,
    # Add ranges to recipient range list and store
    recipient_ranges = db.get(tx.recipient)
    add_range(recipient_ranges, tx_start, tx_end)
    db.put(tx.recipient, recipient_ranges)
    return True

def add_deposit(db, owner, amount, total_deposits):
    owner_ranges = db.get(owner)
    owner_ranges += [total_deposits - amount, total_deposits - 1]
    db.put(owner, owner_ranges)

def validate_tx_sig(tx):
    # TODO: Actually verify the signature
    return True
