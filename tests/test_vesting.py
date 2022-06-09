from brownie.test import given, strategy
from brownie import Wei
import brownie
import random

def test_wrong_create_params(vesting, co, accounts, chain, minter):
    co.transfer(vesting, '1000000 ether', {'from':minter})
    start = chain[-1].timestamp
    recipient = accounts[9]
    with brownie.reverts('Vesting: wrong vehicule parametres'):
        vesting.createVehicule(recipient, 10, 10, start + 200, start + 100, True, {'from':minter})
    with brownie.reverts('Vesting: start cannot be 0'):
        vesting.createVehicule(recipient, 10, 10, 0, start + 100, True, {'from':minter})


# function createVehicule(uint256 _tokenId, uint256 _amount, uint256 _upfront, uint256 _start, uint256 _end)
def test_add_vesting(vesting, co, accounts, chain, minter):
    co.transfer(vesting, '1000000 ether', {'from':minter})
    start = chain[-1].timestamp
    recipient = accounts[9]
    with brownie.reverts('Ownable: caller is not the owner'):
        vesting.createVehicule(recipient, 10, 10, start, start + 100, True, {'from':accounts[1]})

    vesting.createVehicule(recipient, 10, 10, start, start + 100, True, {'from':minter})
    assert vesting.vehiculeCount(recipient) == 1
    assert vesting.vehicules(recipient,0) == (True, start, start + 100, 10, 10, 0, 0)

def test_claim_upfront(vesting, co, accounts, chain, minter):
    co.transfer(vesting, '1000000 ether', {'from':minter})
    start = chain[-1].timestamp
    upfront_claimable = 110
    recipient = accounts[9]
    assert vesting.vehiculeCount(recipient) == 0
    vesting.createVehicule(recipient, 10, upfront_claimable, start, start + 100, True, {'from':minter})
    with brownie.reverts('Vesting: vehicule does not exist'):
        vesting.claim(0, {'from':accounts[2]})
    with brownie.reverts('Vesting: vehicule does not exist'):
        vesting.claim(0, {'from':minter})
    chain.sleep(1)
    chain.mine()
    pre_bal = co.balanceOf(accounts[1])
    vesting.claim(0, {'from':recipient})
    post_bal = co.balanceOf(recipient)
    assert post_bal - pre_bal == upfront_claimable
    vesting.claim(0, {'from':recipient})
    post_post_bal = co.balanceOf(recipient)
    assert post_post_bal == post_bal
    
def test_start_in_future(vesting, co, accounts, chain, minter):
    co.transfer(vesting, '1000000 ether', {'from':minter})
    start = chain[-1].timestamp
    recipient = accounts[9]
    assert vesting.vehiculeCount(recipient) == 0
    vesting.createVehicule(recipient, '100 ether', 0, start + 5000, start + 15000, True, {'from':minter})
    with brownie.reverts('Vesting: vehicule does not exist'):
        vesting.claim(0, {'from':accounts[2]})
    with brownie.reverts('Vesting: vehicule does not exist'):
        vesting.claim(0, {'from':minter})
    with brownie.reverts('Vesting: cliff !started'):
        vesting.claim(0, {'from':recipient})

def test_fully_unlocked(vesting, co, accounts, chain, minter):
    co.transfer(vesting, '1000000 ether', {'from':minter})
    start = chain[-1].timestamp
    claimable = '100 ether'
    recipient = accounts[9]
    assert vesting.vehiculeCount(recipient) == 0
    vesting.createVehicule(recipient, claimable, 0, start , start + 1, True, {'from':minter})
    chain.sleep(10)
    pre_bal = co.balanceOf(recipient)
    vesting.claim(0, {'from':recipient})
    post_bal = co.balanceOf(recipient)
    assert post_bal - pre_bal == claimable

@given(delta=strategy("uint256", min_value=1, max_value=10000000))
def test_claim_some(Vesting, TestToken, accounts, chain, delta):
    minter = accounts[0]
    co = TestToken.deploy({'from':minter})
    vesting =  Vesting.deploy(co, {'from':minter})
    co.transfer(vesting, '1000000 ether', {'from':minter})
    start = chain[-1].timestamp
    maxDelta = 10000000
    claimable = Wei('100 ether')
    recipient = accounts[9]
    assert vesting.vehiculeCount(recipient) == 0
    pre_bal = co.balanceOf(recipient)
    vesting.createVehicule(recipient, claimable, 0, start , start + maxDelta, True, {'from':minter})
    chain.sleep(delta)
    min_expected = claimable * delta // maxDelta
    vesting.claim(0, {'from':recipient})
    post_bal = co.balanceOf(recipient)
    assert post_bal - pre_bal >= min_expected
    assert vesting.claimed(recipient, 0) == post_bal - pre_bal

def min(a, b):
    return a if a < b else b

def test_claim_at_random_until_empty(vesting, co, accounts, chain, minter):
    random.seed()
    co.transfer(vesting, '1000000 ether', {'from':minter})
    start = chain[-1].timestamp
    claimable = '100 ether'
    duration = 100000
    recipient = accounts[9]
    assert vesting.vehiculeCount(recipient) == 0
    vesting.createVehicule(recipient, claimable, 0, start , start + duration, True, {'from':minter})
    elapsed = 0
    total_claimed = 0
    while co.balanceOf(recipient) < '100 ether':
        step = random.randint(1000, 20000)
        elapsed += step
        expected = Wei(claimable) * min(elapsed, duration) // duration - total_claimed
        chain.sleep(step)
        pre_bal = co.balanceOf(recipient)
        vesting.claim(0, {'from':recipient})
        post_bal = co.balanceOf(recipient)
        assert post_bal - pre_bal >= expected
        total_claimed += post_bal - pre_bal
        assert vesting.claimed(recipient, 0) == total_claimed
    assert elapsed >= duration

def test_cannot_end(vesting, co, accounts, chain, minter):
    co.transfer(vesting, '1000000 ether', {'from':minter})
    start = chain[-1].timestamp
    recipient = accounts[9]
    assert vesting.vehiculeCount(recipient) == 0
    vesting.createVehicule(recipient, '100 ether', 0, start + 5000, start + 15000, False, {'from':minter})
    with brownie.reverts('Vesting: Cannot end'):
        vesting.endVehicule(recipient, 0, {'from':minter})
    assert vesting.vehicules(recipient,0) == (False, start + 5000, start + 15000, 0, Wei('100 ether'), 0, 0)

def test_end_vehicule_before_start(vesting, co, accounts, chain, minter):
    co.transfer(vesting, '1000000 ether', {'from':minter})
    start = chain[-1].timestamp
    recipient = accounts[9]
    assert vesting.vehiculeCount(recipient) == 0
    vesting.createVehicule(recipient, '100 ether', 0, start + 5000, start + 15000, True, {'from':minter})
    vesting.endVehicule(recipient, 0, {'from':minter})
    assert vesting.vehicules(recipient,0) == (True, start + 5000, start + 15000, 0, 0, 0, 0)

def test_end_vehicule_after_start(vesting, co, accounts, chain, minter):
    co.transfer(vesting, '1000000 ether', {'from':minter})
    start = chain[-1].timestamp
    recipient = accounts[9]
    assert vesting.vehiculeCount(recipient) == 0
    vesting.createVehicule(recipient, '100 ether', 0, start, start + 15000, True, {'from':minter})
    chain.sleep(7500)
    chain.mine()
    vesting.endVehicule(recipient, 0, {'from':minter})
    (b,s,e,upfront,amount,_,_) =  vesting.vehicules(recipient,0)
    assert e >= start + 7500
    assert amount >= '50 ether'
    chain.sleep(17500)
    chain.mine()
    vesting.claim(0, {'from':recipient})
    assert co.balanceOf(recipient) >= '50 ether' and co.balanceOf(recipient) < Wei('50.5 ether')
    chain.sleep(17500)
    chain.mine()
    vesting.claim(0, {'from':recipient})
    assert co.balanceOf(recipient) >= '50 ether' and co.balanceOf(recipient) < Wei('50.5 ether')


def test_end_vehicule_after_star_after_claims(vesting, co, accounts, chain, minter):
    co.transfer(vesting, '1000000 ether', {'from':minter})
    start = chain[-1].timestamp
    recipient = accounts[9]
    assert vesting.vehiculeCount(recipient) == 0
    vesting.createVehicule(recipient, '100 ether', 0, start, start + 15000, True, {'from':minter})
    chain.sleep(7500 // 2)
    vesting.claim(0, {'from':recipient})
    assert co.balanceOf(recipient) >= Wei('100 ether') // 4
    chain.sleep(7500 // 2)
    chain.mine()
    vesting.endVehicule(recipient, 0, {'from':minter})
    (b,s,e,upfront,amount,_,_) =  vesting.vehicules(recipient,0)
    assert e >= start + 7500
    assert amount >= '50 ether'
    chain.sleep(17500)
    chain.mine()
    vesting.claim(0, {'from':recipient})
    assert co.balanceOf(recipient) >= '50 ether' and co.balanceOf(recipient) < Wei('50.5 ether')
    chain.sleep(17500)
    chain.mine()
    vesting.claim(0, {'from':recipient})
    assert co.balanceOf(recipient) >= '50 ether' and co.balanceOf(recipient) < Wei('50.5 ether')

def test_end_vehicule_after_end(vesting, co, accounts, chain, minter):
    co.transfer(vesting, '1000000 ether', {'from':minter})
    start = chain[-1].timestamp
    recipient = accounts[9]
    assert vesting.vehiculeCount(recipient) == 0
    vesting.createVehicule(recipient, '100 ether', 0, start, start + 15000, True, {'from':minter})
    chain.sleep(15100)
    chain.mine()
    vesting.endVehicule(recipient, 0, {'from':minter})
    (b,s,e,upfront,amount,_,_) =  vesting.vehicules(recipient,0)
    assert e == start + 15000
    assert amount == '100 ether'
    vesting.claim(0, {'from':recipient})
    assert co.balanceOf(recipient) == '100 ether' 
    chain.sleep(17500)
    chain.mine()
    vesting.claim(0, {'from':recipient})
    assert co.balanceOf(recipient) == '100 ether' 
    