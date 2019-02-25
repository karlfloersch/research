def test_erc20_transfers(alice, bob, erc20_ct):
    assert erc20_ct.balanceOf(alice.address) == 1000 and erc20_ct.balanceOf(bob.address) == 1000
    erc20_ct.transferFrom(alice.address, bob.address, 500)
    assert erc20_ct.balanceOf(alice.address) == 500 and erc20_ct.balanceOf(bob.address) == 1500
