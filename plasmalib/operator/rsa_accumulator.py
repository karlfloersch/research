from hashlib import blake2s

def hash(x):
    return blake2s(x).digest()[:32]

def get_primes(givenNumber):
    # Initialize a list
    primes = []
    for possiblePrime in range(2, givenNumber + 1):
        # Assume number is prime until shown it is not.
        isPrime = True
        for num in range(2, int(possiblePrime ** 0.5) + 1):
            if possiblePrime % num == 0:
                isPrime = False
                break
        if isPrime:
            primes.append(possiblePrime)

    return(primes)

def get_B_value(base, result):
    return int.from_bytes(
        hash(base.to_bytes(1024, 'big') + result.to_bytes(1024, 'big')),
        'big'
    )

def prove_exponentiation(base, exponent, result):
    B = get_B_value(base, result)
    b = pow(base, exponent // B, mod)
    remainder = exponent % B
    return (b, remainder)

def verify_proof(base, result, b, remainder):
    B = get_B_value(base, result)
    return pow(b, B, mod) * pow(base, remainder, mod) % mod == result

mod = 25195908475657893494027183240048398571429282126204032027777137836043662020707595556264018525880784406918290641249515082189298559149176184502808489120072844992687392807287776735971418347270261896375014971824691165077613379859095700097330459748808428401797429100642458691817195118746121515172654632282216869987549182422433637259085141865462043576798423387184774447920739934236584823824281198163815010674810451660377306056201619676256133844143603833904414952634432190114657544454178424020924616515723350778707749817125772467962926386356373289912154831438167899885040445364023527381951378636564391212010397122822120720357

acc_values = []

g = 3
acc = g
full_exponent = 1

for v in get_primes(100):
    acc_values.append(v)
    full_exponent = full_exponent * v
    acc = pow(acc, v, mod)
prime_to_prove = acc_values[8]

b, remainder = prove_exponentiation(g, full_exponent, acc)
print(verify_proof(g, acc, b, remainder))
