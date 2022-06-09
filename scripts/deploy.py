from brownie import accounts, Wei, chain, Vesting


def deploy():
	user = accounts.load('ape_deployer', '\0')
	multi_sig = '0x15B513F658f7390D8720dCE321f50974B28672EF'
	co = '0xf828BA501B108FbC6c88eBDfF81C401BB6B94848'

	vesting = Vesting.deploy(co, {'from':user}, publish_source=True)
	vesting.transferOwnership(multi_sig, {'from':user})
