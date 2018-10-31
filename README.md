**WARNING:** this is an experimental project. not for mainnet deployment.

I'm currently in the process of rewriting the client-side construction of inclusion proofs for the exit game. Also, the vyper contract is still missing some challenge mechanisms. **Don't deposit any testnet eth if you plan on keeping it.**

# installation
```
git clone https://github.com/endorphin/plasmaprime.git
cd plasmaprime
pip install -r requirements.txt
```
# client usage
create a new account (send your testnet eth to the created address):
```
cd client
plasma new
```
deposit some test eth (all values are in wei):
```
plasma deposit --contract <address> --amount <value>
```
send a transaction:
```
plasma send --to <address> --amount <value>
```
check your balance (and what ranges you own):
```
plasma query
```
watch for malicious exits (**not yet implemented**):
```
plasma guard
```
withdraw:
```
plasma exit --amount <value>
```
# protocol
transaction format:
```
{
    sender: address,
    recipient: address,
    start: uint,
    offset: uint,
    signature: {
        sig_v: uint,
        sig_r: uint,
        sig_s: uint,
    },
}
```
# todo
- challenges for exits that include coins previously exited
- challenges for transaction history
- challenges for subsequent spends
- implement plasma guard
- concise exclusion proofs with RSA accumulators
- proper merkle sum tree
