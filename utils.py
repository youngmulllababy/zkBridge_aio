import json
import time
from web3 import Web3
import requests
from fake_useragent import UserAgent
from loguru import logger
from eth_account.messages import encode_defunct
from tqdm import tqdm
from moralis import evm_api
import pandas as pd
from info import *
from config import *
from eth_utils import *

class Help:
    def check_status_tx(self,tx_hash,):
        logger.info(f'{self.address} - жду подтверждения транзакции...')

        start_time = int(time.time())
        while True:
            current_time = int(time.time())
            if current_time >= start_time + max_wait_time:
                logger.info(f'{self.address} - транзакция не подтвердилась за {max_wait_time} cекунд, начинаю повторную отправку...')
                return 0
            try:
                status = self.w3.eth.get_transaction_receipt(tx_hash)['status']
                if status in [0, 1]:
                    return status
                time.sleep(1)
            except Exception as error:
                time.sleep(1)
    def sleep_indicator(self, sec):
        for i in tqdm(range(sec), desc='жду', bar_format="{desc}: {n_fmt}c /{total_fmt}c {bar}", colour='green'):
            time.sleep(1)

class ZkBridge(Help):
    def __init__(self,privatekey,delay,chain, to, api, mode, proxy=None):
        self.privatekey = privatekey
        self.chain = chain
        self.to = to
        self.w3 = Web3(Web3.HTTPProvider(rpcs[self.chain]))
        self.account = self.w3.eth.account.from_key(self.privatekey)
        self.address = self.account.address
        self.nft = nft
        self.delay = delay
        self.proxy = proxy
        self.mode = mode
        self.gwei = gwei
        self.moralisapi = api
        self.nft_address = nfts_addresses[self.nft][self.chain] if self.mode == 1 else reversed_nfts_addresses[self.nft][self.chain]
        self.bridge_address = nft_bridge_addresses[self.chain]
    def auth(self):
        ua = UserAgent()
        ua = ua.random
        headers = {
            'authority': 'api.zkbridge.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json',
            'origin': 'https://zkbridge.com',
            'referer': 'https://zkbridge.com/',
            'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': ua,
        }

        json_data = {
            'publicKey': self.address.lower(),
        }

        while True:
            try:
                if self.proxy:
                    proxies = {'http': self.proxy, 'https': self.proxy}
                    response = requests.post(
                        'https://api.zkbridge.com/api/signin/validation_message',
                        json=json_data, headers=headers, proxies=proxies
                    )
                else:
                    response = requests.post(
                        'https://api.zkbridge.com/api/signin/validation_message',
                        json=json_data, headers=headers,

                    )

                if response.status_code == 200:
                    msg = json.loads(response.text)

                    msg = msg['message']
                    msg = encode_defunct(text=msg)
                    sign = self.w3.eth.account.sign_message(msg, private_key=self.privatekey)
                    signature = self.w3.to_hex(sign.signature)
                    json_data = {
                        'publicKey': self.address,
                        'signedMessage': signature,
                    }
                    return signature, ua
            except Exception as e:
                logger.error(f'{self.address}:{self.chain} - {e}')
                time.sleep(5)
    def sign(self):

        # sign msg
        signature, ua = self.auth()
        headers = {
            'authority': 'api.zkbridge.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json',
            'origin': 'https://zkbridge.com',
            'referer': 'https://zkbridge.com/',
            'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': ua,
        }

        json_data = {
            'publicKey': self.address.lower(),
            'signedMessage': signature,
        }
        while True:
            try:

                if self.proxy:
                    proxies = {'http': self.proxy, 'https': self.proxy}

                    response = requests.post('https://api.zkbridge.com/api/signin', headers=headers, json=json_data,
                                             proxies=proxies)
                else:
                    response = requests.post('https://api.zkbridge.com/api/signin', headers=headers, json=json_data)
                if response.status_code == 200:
                    token = json.loads(response.text)['token']
                    headers['authorization'] = f'Bearer {token}'
                    session = requests.session()
                    session.headers.update(headers)
                    return session

            except Exception as e:
                logger.error(F'{self.address}:{self.chain} - {e}')
                time.sleep(5)
    def profile(self):
        session = self.sign()
        params = ''
        try:
            if self.proxy:
                proxies = {'http': self.proxy, 'https': self.proxy}
                response = session.get('https://api.zkbridge.com/api/user/profile', params=params, proxies=proxies)
            else:
                response = session.get('https://api.zkbridge.com/api/user/profile', params=params)
            if response.status_code == 200:
                logger.success(f'{self.address}:{self.chain} - успешно авторизовался...')
                return session
        except Exception as e:
            logger.error(f'{self.address}:{self.chain} - {e}')
            return False
    def balance_and_get_id(self):
        try:
            api_key = self.moralisapi
            params = {
                "chain": self.chain,
                "format": "decimal",
                "token_addresses": [
                    self.nft_address
                ],
                "media_items": False,
                "address": self.address}

            result = evm_api.nft.get_wallet_nfts(api_key=api_key, params=params)
            id_ = int(result['result'][0]['token_id'])
            if id_:
                logger.success(f'{self.address}:{self.chain} - успешно найдена {self.nft} {id_}...')
                return id_

        except Exception as e:
            if 'list index out of range' in str(e):
                logger.error(f'{self.address}:{self.chain} - на кошельке отсутсвует {self.nft}...')
                return None
            else:
                logger.error(f'{self.address}:{self.chain} - {e}...')
    def mint(self, gwei=None):
        while True:
            zkNft = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.nft_address), abi=zk_nft_abi)

            session = self.profile()
            if not session:
                return False
            try:
                if session:
                    nonce = self.w3.eth.get_transaction_count(self.address)
                    time.sleep(2)
                    tx = zkNft.functions.mint().build_transaction({
                        'from': self.address,
                        'gas': zkNft.functions.mint().estimate_gas(
                            {'from': self.address, 'nonce': nonce}),
                        'nonce': nonce,
                        'gasPrice': self.w3.eth.gas_price
                    })

                    if self.chain != 'bsc':
                        tx['gasPrice'] = self.w3.eth.gas_price
                    else:
                        gwei = self.gwei
                        tx['gasPrice'] = int(gwei * 10 ** 9)

                    logger.info(f'{self.address}:{self.chain} - начинаю минт {self.nft}...')
                    sign = self.account.sign_transaction(tx)
                    hash = self.w3.eth.send_raw_transaction(sign.rawTransaction)
                    status = self.check_status_tx(hash)
                    self.sleep_indicator(5)
                    if status == 1:
                        logger.success(f'{self.address}:{self.chain} - успешно заминтил {self.nft} : {scans[self.chain]}{self.w3.to_hex(hash)}...')
                        self.sleep_indicator(random.randint(self.delay[0], self.delay[1]))
                        return session
                    else:
                        gwei = gwei*1.2
                        logger.info(f'{self.address}:{self.chain} - пробую минтить с увеличенным газом : {gwei} gwei...')
                        self.mint(gwei)
            except Exception as e:
                error = str(e)
                if 'INTERNAL_ERROR: insufficient funds' in error or 'insufficient funds for gas * price + value' in error:
                    logger.error(f'{self.address}:{self.chain} - не хватает денег на газ, заканчиваю работу через 5 секунд...')
                    time.sleep(5)
                    return False
                if 'Each address may claim one NFT only. You have claimed already' in error:
                    logger.error(f'{self.address}:{self.chain} - {self.nft} можно клеймить только один раз!...')
                    return False
                else:
                    logger.error(f'{self.address}:{self.chain} - {e}...')
                    return False
    def bridge_nft(self):
        if self.mode == 1: #mode 1 - mint&bridge  /  mode 0 - find nft and bridge
            session = self.mint()
            if session:
                id_ = self.balance_and_get_id()
                pass
            else:
                return False
        else:
            session = self.profile()
            id_ = self.balance_and_get_id()

        if id_ == None:
            return False

        zkNft = self.w3.eth.contract(address=Web3.to_checksum_address(self.nft_address), abi=zk_nft_abi)

        def approve_nft(gwei=None):
            # approve
            while True:
                if id_:
                    try:
                        nonce = self.w3.eth.get_transaction_count(self.address)
                        time.sleep(2)
                        tx = zkNft.functions.approve(
                            Web3.to_checksum_address(self.bridge_address), id_).build_transaction({
                            'from': self.address,
                            'gas': zkNft.functions.approve(Web3.to_checksum_address(self.bridge_address),
                                                           id_).estimate_gas(
                                {'from': self.address, 'nonce': nonce}),
                            'nonce': nonce,
                            'gasPrice': self.w3.eth.gas_price

                        })

                        if self.chain != 'bsc':
                            tx['gasPrice'] = self.w3.eth.gas_price
                        else:
                            tx['gasPrice'] = int(self.gwei * 10 ** 9)

                        logger.info(f'{self.address}:{self.chain} - начинаю апрув {self.nft} {id_}...')
                        sign = self.account.sign_transaction(tx)
                        hash = self.w3.eth.send_raw_transaction(sign.rawTransaction)
                        status = self.check_status_tx(hash)
                        self.sleep_indicator(5)
                        if status == 1:
                            logger.success(
                                f'{self.address}:{self.chain} - успешно апрувнул {self.nft} {id_} : {scans[self.chain]}{self.w3.to_hex(hash)}...')
                            self.sleep_indicator(random.randint(1, 10))
                            return True
                        else:
                            if self.chain == 'bsc':
                                self.gwei = self.gwei * 1.2
                                logger.info(f'{self.address}:{self.chain} - пробую апрувать с увеличенным газом : {self.gwei} gwei...')
                                approve_nft(self.gwei)

                    except Exception as e:
                        error = str(e)
                        if 'INTERNAL_ERROR: insufficient funds' in error or 'insufficient funds for gas * price + value' in error:
                            logger.error(
                                f'{self.address}:{self.chain} - не хватает денег на газ, заканчиваю работу через 5 секунд...')
                            time.sleep(5)
                            return False
                        else:
                            logger.error(f'{self.address}:{self.chain} - {e}...')
                            time.sleep(2)
                            return False

        def bridge_(gwei=None):
            bridge = self.w3.eth.contract(address=Web3.to_checksum_address(self.bridge_address), abi=bridge_abi)
            to = chain_ids[self.to]
            fee = bridge.functions.fee(to).call()
            logger.info(f'{self.address}:{self.chain} - начинаю бридж {self.nft} {id_}...')
            while True:
                try:
                    enco = f'0x000000000000000000000000{self.address[2:]}'
                    nonce = self.w3.eth.get_transaction_count(self.address)
                    time.sleep(2)
                    tx = bridge.functions.transferNFT(
                        Web3.to_checksum_address(self.nft_address), id_, to,
                        enco).build_transaction({
                        'from': self.address,
                        'value': fee,
                        'gas': bridge.functions.transferNFT(
                            Web3.to_checksum_address(self.nft_address), id_, to,
                            enco).estimate_gas(
                            {'from': self.address, 'nonce': nonce, 'value': fee}),
                        'nonce': nonce,
                        'gasPrice': self.w3.eth.gas_price
                    })

                    if self.chain != 'bsc':
                        tx['gasPrice'] = self.w3.eth.gas_price
                    else:
                        tx['gasPrice'] = int(self.gwei * 10 ** 9)

                    sign = self.account.sign_transaction(tx)
                    hash = self.w3.eth.send_raw_transaction(sign.rawTransaction)
                    status = self.check_status_tx(hash)
                    self.sleep_indicator(5)
                    if status == 1:
                        logger.success(
                            f'{self.address}:{self.chain} - успешно бриджанул {self.nft} {id_} : {scans[self.chain]}{self.w3.to_hex(hash)}...')
                        self.sleep_indicator(random.randint(1, 20))
                        return self.w3.to_hex(hash), session, id_
                    else:
                        if self.chain == 'bsc':
                            self.gwei = self.gwei * 1.2
                            logger.info(f'{self.address}:{self.chain} - пробую бриджить с увеличенным газом : {self.gwei} gwei...')
                            bridge_(self.gwei)

                except Exception as e:
                    error = str(e)
                    if 'INTERNAL_ERROR: insufficient funds' in error or 'insufficient funds for gas * price + value' in error:
                        logger.error(
                            f'{self.address}:{self.chain} - не хватает денег на газ, заканчиваю работу через 5 секунд...')
                        time.sleep(5)
                        return False
                    else:
                        logger.error(f'{self.address}:{self.chain} - {e}')
                        return False

        if approve_nft(self):
            return bridge_()
    def go_requests(self, hash, session, nft_id):
        def create_order():
            json_data = {
                'from': self.address.lower(),
                'to': self.address.lower(),
                'sourceChainId': ids[self.chain],
                'targetChainId': ids[self.to],
                'txHash': hash,
                'contracts': [
                    {
                        'contractAddress': self.nft_address,
                        'tokenId': nft_id,
                    },
                ],
            }
            while True:
                try:
                    if self.proxy:
                        proxies = {'http': self.proxy, 'https': self.proxy}
                        response = session.post('https://api.zkbridge.com/api/bridge/createOrder', json=json_data,
                                                proxies=proxies)
                    else:
                        response = session.post('https://api.zkbridge.com/api/bridge/createOrder', json=json_data)
                    if response.status_code == 200:
                        id_ = json.loads(response.text)['id']
                        return id_
                except Exception as e:
                    logger.error(f'{self.address}:{self.chain}- {e}')
                    time.sleep(5)

        def gen_blob():
            data = create_order()
            if data:
                id_ = data
            else:
                return False
            json_data = {
                'tx_hash': hash,
                'chain_id': chain_ids[self.chain],
                'testnet': False,
            }
            while True:
                try:
                    if self.proxy:
                        proxies = {'http': self.proxy, 'https': self.proxy}
                        response = session.post('https://api.zkbridge.com/api/v2/receipt_proof/generate', json=json_data,
                                                proxies=proxies)
                    else:
                        response = session.post('https://api.zkbridge.com/api/v2/receipt_proof/generate', json=json_data)
                    if response.status_code == 200:
                        data_ = json.loads(response.text)
                        logger.success(f'{self.address} - сгенерирован blob...')
                        return data_, id_, session

                except Exception as e:
                    logger.error(f'{self.address}:{self.to}- {e}')
                    time.sleep(5)
        return gen_blob()
    def claimOrder(self, session, id, hash):
        json_data = {
            'claimHash': hash,
            'id': id,
        }
        while True:
            try:
                if self.proxy:
                    proxies = {'http': self.proxy, 'https': self.proxy}
                    response = session.post('https://api.zkbridge.com/api/bridge/claimOrder', json=json_data,
                                            proxies=proxies)
                else:
                    response = session.post('https://api.zkbridge.com/api/bridge/claimOrder', json=json_data)
                if response.status_code == 200:
                    logger.success(f'{self.address} - успешно забриджено!...')
                    self.sleep_indicator(random.randint(self.delay[0], self.delay[1]))
                    return True

            except Exception as e:
                logger.error(f'{self.address}:{self.to}- {e}')
                time.sleep(5)
    def check_status_tx2(self, w3, tx_hash, ):
        logger.info(f'{self.address} - жду подтверждения транзакции...')
        start_time = int(time.time())
        while True:
            current_time = int(time.time())
            try:
                status = w3.eth.get_transaction_receipt(tx_hash)['status']
                if status in [0, 1]:
                    return status
                if current_time >= start_time + max_wait_time:
                    logger.info(
                        f'{self.address} - транзакция не подтвердилась за {max_wait_time} cекунд, начинаю повторную отправку...')
                    return 0
                time.sleep(1)
            except Exception as error:
                time.sleep(1)
    def claim_on_destinaton(self, gasPrice=None):
        if self.to == 'bsc':
            rpc = 'https://bscrpc.com'
        else:
            rpc = rpcs[self.to]
        w3 = Web3(Web3.HTTPProvider(rpc))
        account = w3.eth.account.from_key(self.privatekey)
        address = account.address
        claim = w3.eth.contract(address=Web3.to_checksum_address(nft_claim_addresses[self.to]),abi=zk_claim_abi)

        data = self.bridge_nft()
        if data:
            hash_, session, nft_id = data
        else:
            return address, False

        while True:
            data = self.go_requests(hash_, session, nft_id)
            if data:
                data_, id_, session = data
            else:
                return address, False
            cid = data_['chain_id']
            proof = data_['proof_index']
            blob = data_['proof_blob']
            block_hash = data_['block_hash']
            try:
                nonce = w3.eth.get_transaction_count(address)
                time.sleep(2)
                gasPrice = w3.eth.gas_price
                tx = claim.functions.validateTransactionProof(cid,to_bytes(hexstr=block_hash), proof,to_bytes(hexstr=blob)).build_transaction({
                    'from': address,
                    'gas': claim.functions.validateTransactionProof(cid,to_bytes(hexstr=block_hash), proof,to_bytes(hexstr=blob)).estimate_gas(
                        {'from': address, 'nonce': nonce}),
                    'nonce': nonce,
                    'gasPrice': gasPrice
                })

                sign = account.sign_transaction(tx)
                hash = w3.eth.send_raw_transaction(sign.rawTransaction)
                status = self.check_status_tx2(w3, hash)
                self.sleep_indicator(10)
                if status == 1:
                    logger.success(f'{address}:{self.to} - успешно заклеймил {self.nft} : {scans[self.to]}{w3.to_hex(hash)}...')
                    self.sleep_indicator(random.randint(1, 20))  # delay
                    order = self.claimOrder(session, id_, block_hash)
                    if order:
                        return address, 'success'
                    else:
                        return address, 'error'
                else:
                    gasPrice = gasPrice * 1.2
                    logger.info( f'{self.address}:{self.chain} - пробую клеймить с увеличенным газом : {gasPrice/10**9} gwei...')
                    self.claim_on_destinaton(gasPrice)

            except Exception as e:
                error = str(e)
                if 'execution reverted: Block Header is not set' in error:
                    logger.info(f'{address}:{self.to} - {self.to} лагает, пробую еще раз...')
                    tt = random.randint(20,60)
                    logger.info(f'{address}:{self.to} - cплю {tt} секунд...')
                    self.sleep_indicator(tt)
                elif 'INTERNAL_ERROR: insufficient funds' in error or 'insufficient funds for gas * price + value' in error:
                    logger.error(f'{self.address}:{self.to} - не хватает денег на газ, заканчиваю работу через 5 секунд...')
                    time.sleep(5)
                    return address, 'error'
                elif 'Message already executed' in error:
                    logger.success(f'{self.address}:{self.to} - успешно заклеймил {self.nft}...')
                    return address, 'success'
                else:
                    logger.error(f'{address}:{self.to} - {e} ...')
                    return address, 'error'

class ZkMessage(Help):
    def __init__(self, privatekey, chain, to, delay, proxy=None):
        self.privatekey = privatekey
        self.chain = chain
        self.to = to
        self.w3 = Web3(Web3.HTTPProvider(rpcs[self.chain]))
        self.scan = scans[self.chain]
        self.account = self.w3.eth.account.from_key(self.privatekey)
        self.address = self.account.address
        self.delay = delay
        self.gwei = gwei
        self.proxy = proxy
    def auth(self):
        ua = UserAgent()
        ua = ua.random
        headers = {
            'authority': 'api.zkbridge.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json',
            'origin': 'https://zkbridge.com',
            'referer': 'https://zkbridge.com/',
            'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': ua,
        }

        json_data = {
            'publicKey': self.address.lower(),
        }

        while True:
            try:
                if self.proxy:
                    proxies = {'http': self.proxy, 'https': self.proxy}
                    response = requests.post(
                        'https://api.zkbridge.com/api/signin/validation_message',
                        json=json_data,     headers=headers,proxies=proxies
                    )
                else:
                    response = requests.post(
                        'https://api.zkbridge.com/api/signin/validation_message',
                        json=json_data,    headers=headers,

                    )

                if response.status_code == 200:
                    msg = json.loads(response.text)

                    msg = msg['message']
                    msg = encode_defunct(text=msg)
                    sign = self.w3.eth.account.sign_message(msg, private_key=self.privatekey)
                    signature = self.w3.to_hex(sign.signature)
                    json_data = {
                        'publicKey': self.address,
                        'signedMessage': signature,
                    }
                    return signature, ua
            except Exception as e:
                logger.error(f'{self.address}:{self.chain} - {e}')
                time.sleep(5)
    def sign(self):

        # sign msg
        signature, ua = self.auth()
        headers = {
            'authority': 'api.zkbridge.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json',
            'origin': 'https://zkbridge.com',
            'referer': 'https://zkbridge.com/',
            'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': ua,
        }

        json_data = {
            'publicKey': self.address.lower(),
            'signedMessage': signature,
        }
        while True:
            try:

                if self.proxy:
                    proxies = {'http': self.proxy, 'https': self.proxy}

                    response = requests.post('https://api.zkbridge.com/api/signin', headers=headers, json=json_data, proxies=proxies)
                else:
                    response = requests.post('https://api.zkbridge.com/api/signin',  headers=headers, json=json_data)
                if response.status_code == 200:
                    token = json.loads(response.text)['token']
                    headers['authorization'] = f'Bearer {token}'
                    session = requests.session()
                    session.headers.update(headers)
                    return session

            except Exception as e:
                logger.error(F'{self.address}:{self.chain} - {e}')
                time.sleep(5)
    def profile(self):
        session = self.sign()
        params = ''
        try:
            if self.proxy:
                proxies = {'http': self.proxy, 'https': self.proxy}
                response = session.get('https://api.zkbridge.com/api/user/profile', params=params,proxies=proxies)
            else:
                response = session.get('https://api.zkbridge.com/api/user/profile', params=params)
            if response.status_code == 200:
                logger.success(f'{self.address}:{self.chain} - успешно авторизовался...')
                return session
        except Exception as e:
            logger.error(f'{self.address}:{self.chain} - {e}')
            return False
    def msg(self, session, contract_msg, msg, from_chain, to_chain,tx_hash):

        timestamp = time.time()

        json_data = {
            'message': msg,
            'mailSenderAddress': contract_msg,
            'receiverAddress': self.address,
            'receiverChainId': to_chain,
            'sendTimestamp': timestamp,
            'senderAddress': self.address,
            'senderChainId': from_chain,
            'senderTxHash': tx_hash,
            'sequence': random.randint(4500,5000),
            'receiverDomainName': '',
        }

        try:
            if self.proxy:
                proxies = {'http': self.proxy, 'https': self.proxy}
                response = session.get('https://api.zkbridge.com/api/user/profile', json=json_data,proxies=proxies)
            else:
                response = session.get('https://api.zkbridge.com/api/user/profile', json=json_data)
            if response.status_code == 200:
                logger.success(f'{self.address}:{self.chain} - cообщение подтвержденно...')
                return True


        except Exception as e:
            logger.error(f'{self.address}:{self.chain} - {e}')
            return False
    def create_msg(self):
        n = random.randint(1, 10)
        string = []
        word_site = "https://www.mit.edu/~ecprice/wordlist.10000"
        response = requests.get(word_site)
        for i in range(n):
            WORDS = [g for g in response.text.split()]
            string.append(random.choice(WORDS))

        msg = ' '.join(string)
        return msg
    def send_msg(self,gwei=None):
        data = self.profile()
        if data:
            session = data
        else:
            return False
        contract_msg = Web3.to_checksum_address(sender_msgs[self.chain])
        lz_id = stargate_ids[self.to]
        to_chain_id = chain_ids[self.to]
        from_chain_id = chain_ids[self.chain]
        message = self.create_msg()
        dst_address = Web3.to_checksum_address(dst_addresses[self.to])
        lzdst_address = Web3.to_checksum_address(lzdst_addresses[self.to])

        mailer = self.w3.eth.contract(address=contract_msg,abi=mailer_abi)
        while True:
            try:
                tx = mailer.functions.sendMessage(to_chain_id,dst_address,lz_id,lzdst_address,0,self.address,message).build_transaction({
                    'from': self.address,
                    'value':fee_for_message[self.chain],
                    'gas':mailer.functions.sendMessage(to_chain_id,dst_address,lz_id,lzdst_address,0,self.address,message).estimate_gas({'from': self.address, 'nonce': self.w3.eth.get_transaction_count(self.address),'value':fee_for_message[self.chain]}),
                    'nonce': self.w3.eth.get_transaction_count(self.address),
                    'gasPrice': self.w3.eth.gas_price
                })

                if self.chain != 'bsc':
                    tx['gasPrice'] = self.w3.eth.gas_price
                else:
                    tx['gasPrice'] = int(self.gwei * 10 ** 9)

                logger.info(f'{self.address}:{self.chain} - начинаю отправку сообщения в {self.to}...')
                sign = self.account.sign_transaction(tx)
                hash = self.w3.eth.send_raw_transaction(sign.rawTransaction)
                status = self.check_status_tx(hash)
                self.sleep_indicator(5)
                if status == 1:
                    logger.success(f'{self.address}:{self.chain} - успешно отправил сообщение {message} в {self.to} : {self.scan}{self.w3.to_hex(hash)}...')
                    time.sleep(5)
                    msg = self.msg(session,contract_msg,message,from_chain_id,to_chain_id,self.w3.to_hex(hash))
                    if msg:
                        self.sleep_indicator(random.randint(self.delay[0],self.delay[1]))
                        return self.address, 'success'
                else:
                    if self.chain == 'bsc':
                        self.gwei = self.gwei * 1.2
                        logger.info(f'{self.address}:{self.chain} - пробую отправлять сообщение с увеличенным газом : {self.gwei} gwei...')
                        self.send_msg(self.gwei)

            except Exception as e:
                error = str(e)
                if 'INTERNAL_ERROR: insufficient funds' in error or 'insufficient funds for gas * price + value' in error:
                    logger.error(f'{self.address}:{self.chain} - не хватает денег на газ, заканчиваю работу через 5 секунд...')
                    time.sleep(5)
                    return self.address, 'error'
                else:
                    logger.error(f'{self.address}:{self.chain} - {e}...')
                    return self.address, 'error'