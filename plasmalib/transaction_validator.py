import bisect

def subtract_range(range_list, start, end):
    affected_range = None
    for i in range(0, len(range_list), 2):
        r_start = range_list[i]
        r_end = range_list[i+1]
        if r_start <= start and end <= r_end:
            affected_range = i
            break
    if affected_range is None:
        return False
    # Remove the effected range
    del range_list[i:i + 2]
    # Create new sub-ranges based on what we deleted
    if r_start < start:
        # range_list += [r_start, start - 1]
        insertion_point = bisect.bisect_left(range_list, r_start)
        range_list[insertion_point:insertion_point] = [r_start, start - 1]
    if r_end > end:
        # range_list += [end + 1, r_end]
        insertion_point = bisect.bisect_left(range_list, end + 1)
        range_list[insertion_point:insertion_point] = [end + 1, r_end]
    return True


def add_range(range_list, start, end):
    # Find left_range (a range which ends at the start of our tx) and right_range (a range which starts at the end of our tx)
    left_range = None
    right_range = None
    insertion_point = bisect.bisect_left(range_list, start)
    if range_list[insertion_point - 1] == start - 1:
        left_range = insertion_point - 2
    if insertion_point < len(range_list) and range_list[insertion_point] == end + 1:
        right_range = insertion_point
    # Set the start and end of our new range based on the deleted ranges
    if left_range is not None:
        start = range_list[left_range]
    if right_range is not None:
        end = range_list[right_range + 1]
    # Delete the left_range and right_range if we found them
    if left_range is not None and right_range is not None:
        del range_list[left_range + 1:right_range + 1]
        return
    elif left_range is not None:
        del range_list[left_range:left_range + 2]
        insertion_point -= 2
    elif right_range is not None:
        del range_list[right_range:right_range + 2]
    range_list[insertion_point:insertion_point] = [start, end]

def add_tx(db, tx):
    # Now make sure the range is owned by the sender
    sender_ranges = db.get(tx.sender)
    tx_start = tx.start
    tx_end = tx.start + tx.offset - 1
    # Subtract ranges from sender range list and store
    if not subtract_range(sender_ranges, tx_start, tx_end):
        return False
    db.put(tx.sender, sender_ranges)
    # After having deleted the sender ranges,
    # Add ranges to recipient range list and store
    recipient_ranges = db.get(tx.recipient)
    add_range(recipient_ranges, tx_start, tx_end)
    db.put(tx.recipient, recipient_ranges)
    return sender_ranges

def add_deposit(db, owner, amount):
    total_deposits = db.get('total_deposits')
    if total_deposits is None:
        total_deposits = 0
    owner_ranges = db.get(owner)
    if owner_ranges is None:
        owner_ranges = []
    owner_ranges += [total_deposits, total_deposits + amount - 1]
    total_deposits += amount
    db.put(owner, owner_ranges)
    db.put('total_deposits', total_deposits)
    return owner_ranges

def validate_tx_sig(tx):
    # TODO: Actually verify the signature
    return True
