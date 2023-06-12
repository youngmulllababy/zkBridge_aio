import random

'''
в proxyy прокси с новой строки в формате - http://login:pass@ip:port
в keys приватники с новой строки
delay - от и до скольки секунд между кошельками
moralis api key - https://admin.moralis.io/login регаемся и получаем апи ключ
max_wait_time - cколько максимум по времени ждать в секундах подтверждения транзакции 
ваш гвей (чем ниже тем дольше)
'''
with open("keys.txt", "r") as f:
    keys = [row.strip() for row in f]
    random.shuffle(keys)

with open("proxyy.txt", "r") as f:
    proxies = [row.strip() for row in f]

DELAY = (0, 100)

MORALIS_API_KEY = ''

max_wait_time = 100

gwei = 1.5

'''
    MESSENGER  -  chain  только из bsc или polygon
                  to  только bsc, polygon, или ftm


    NFTBRIDGER - для каждой нфт свои чейны, если ошибетесь - работать не будет

    данные ниже для работы в режиме 1 (режим минта & бриджа)

    greenfield   -   сhain - bsc  to - polygon
    zkLightClient   -   сhain - bsc, polygon  to - bsc, polygon
    Mainnet Alpha   -   сhain - polygon  to - bsc
    Luban   -   сhain - bsc  to - polygon

    данные ниже для работы в режиме 0 (режим бриджа УЖЕ ЗАБРИДЖЕННЫХ КОГДА ТО НФТ)

    greenfield   -   сhain - polygon  to - bsc
    zkLightClient   -   сhain - bsc, polygon  to - bsc, polygon
    Mainnet Alpha   -   сhain - bsc  to - polygon 
    Luban   -   сhain - polygon  to - bsc
    
    TYPE - messenger / nftbridger (выбираете свой тип)
    
    MODE 0/1   1 (режим минта & бриджа) / 0 (режим бриджа УЖЕ ЗАБРИДЖЕННЫХ КОГДА ТО НФТ)
    
    NFT - ВЫБОР НАЗВАНИЯ НФТ
'''

TYPE = 'messenger'   # 'messenger' / 'nftbridger'
#chains - bsc / polygon / ftm
chain = 'bsc'
to = 'polygon'
MODE = 1   #mode 1 - mint&bridge 0 - bridge already minted nfts

nft = 'Luban'  #'greenfield' 'zkLightClient' 'Mainnet Alpha' 'Luban' /  random.choice['greenfield','zkLightClient','Mainnet Alpha','Luban']  - random nft
