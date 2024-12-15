import asyncio
from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.exceptions import TransactionNotFound
import json
import aiofiles
from web3 import AsyncWeb3, AsyncHTTPProvider, Web3



class Wallet:
    def __init__(self, private_key, rpc_url, contract_address, abi_path,value):
        self.private_key = private_key
        self.rpc_url = rpc_url
        self.w3 = AsyncWeb3(AsyncHTTPProvider(self.rpc_url))
        self.address = self.w3.eth.account.from_key(self.private_key).address
        self.contract_address = self.w3.to_checksum_address(contract_address)
        self.contract = None
        self.abi_path = abi_path
        self.value = value


    async def load_contract(self):
        async with aiofiles.open(self.abi_path, 'r') as abi_file:
            abi = json.loads(await abi_file.read())
            self.contract = self.w3.eth.contract(address=self.contract_address, abi=abi)



    async def qoter(self,outtoken,slippage):
        async with aiofiles.open(self.abi_path, 'r') as abi_file:
            abi = json.loads(await abi_file.read())
            self.contract = self.w3.eth.contract(address=self.contract_address, abi=abi)
            path = ["0x82aF49447D8a07e3bd95BD0d56f35241523fBab1", outtoken]
            qot = await self.contract.functions.getAmountsOut(self.value,path).call()
            amount_out_min = qot[-1]
            amount_out_min = int(amount_out_min * (1 - slippage))
            return amount_out_min

    async def fetch_balances(self):
        balance_eth = await self.w3.eth.get_balance(self.address)
        return f"eth: {self.w3.from_wei(balance_eth, 'ether')}"

    async def need_balance(self):
        balance_eth = await self.w3.eth.get_balance(self.address)
        balance = self.w3.from_wei(balance_eth, 'ether')
        if float(balance) - float(self.w3.from_wei(self.value, 'ether')) <= 0:
            print("Не хватает эфира для свопа")
            exit()

    async def swap(self,intoken,outtoken):
        latest_block = await self.w3.eth.get_block('latest')  # Дождитесь выполнения корутины
        block_timestamp = latest_block['timestamp']  # Получите значение timestamp
        expiration_time = block_timestamp + 60 * 20  # Добавьте 20 минут
        path = [intoken, outtoken] ##############################################
        print(path)
        async with aiofiles.open(self.abi_path, 'r') as abi_file:
            abi = json.loads(await abi_file.read())
            self.contract = self.w3.eth.contract(address=self.contract_address, abi=abi)
        tx = await self.contract.functions.swapExactETHForTokens(
            await self.qoter(outtoken,slippage),
            path,
            self.address,
            expiration_time
        ).build_transaction({
            "chainId": int(await self.w3.eth.chain_id),
            "from": self.address,
            "nonce": await self.w3.eth.get_transaction_count(self.address),
            "maxFeePerGas": int(await self.w3.eth.gas_price * 1.25 + await self.w3.eth.max_priority_fee),
            "maxPriorityFeePerGas": await self.w3.eth.max_priority_fee,
        })

        # Оценка газа
        tx["gas"] = int((await self.w3.eth.estimate_gas(tx)) * 1.5)

        # Подписание транзакции
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)

        # Отправка транзакции
        return await self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)


int(1 * 10**18)
private_key= ""
rpc_url= "https://rpc.ankr.com/arbitrum/64354c6eecd1f73dadedaccbc1dda76b95cceb1582a6a07c03c9b9c20198b965"
contract_address= "0x4752ba5DBc23f44D87826276BF6Fd6b1C372aD24"
abi_path= "abi.json"
eth = 0.001 # Количество эфира для свопа
value = Web3.to_wei(eth, 'ether')
slippage = 0.01
exp = "https://arbiscan.io/tx/"
intoken= Web3.to_checksum_address("0x82aF49447D8a07e3bd95BD0d56f35241523fBab1")#####"0x0000000000000000000000000000000000000000"
outtoken = Web3.to_checksum_address("0xaf88d065e77c8cC2239327C5EDb3A432268e5831")
async def main():
    wallet = Wallet(private_key, rpc_url, contract_address, abi_path,value)

    #await wallet.load_contract()

    await wallet.need_balance()

    await wallet.qoter(outtoken, slippage)

    #await wallet.odos_transfer(intoken,outtoken)


#     await wallet.need_balance(wallet.address, value)
#
#     sender_balances = await wallet.fetch_balances(wallet.address)
#     print(f"Баланс отправителя: {sender_balances}")
#
#
    try:
        tx_hash = await wallet.swap(intoken,outtoken)
        print(f"Транзакция отправлена: {exp}{tx_hash.hex()}")
    except Exception as e:
        print(f"Ошибка при отправке транзакции: {e}")
#
asyncio.run(main())
