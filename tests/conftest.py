import pytest


# @pytest.fixture(scope="function", autouse=True)
# def shared_setup(fn_isolation):
#     pass


@pytest.fixture()
def minter(accounts):
    return accounts[0]


@pytest.fixture()
def receiver(accounts):
    return accounts[2]

@pytest.fixture()
def co(TestToken, minter):
    return TestToken.deploy({'from':minter})

@pytest.fixture()
def vesting(Vesting, co, minter):
    return Vesting.deploy(co, {'from':minter})

