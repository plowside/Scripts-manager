import asyncio, httpx

import requests, json

req = requests.post(f'http://localhost/api/encrypt', params={'action': 'encrypt'}, files={'project_uuid': (None, '0f617dc0-b4c0-4301-833e-b497ecfc4abb'), 'files_to_encrypt': (None, json.dumps({"config.py":0,"main.py":2,"routers.py":0}))})
print(req.json())
exit()

async def test():
	async with httpx.AsyncClient() as client:
		#{'ulr': 'http://localhost/api/encrypt', 'params': {'action': 'encrypt', 'project_uuid': '0f617dc0-b4c0-4301-833e-b497ecfc4abb'}, 'files': {'files_to_encrypt': '{"config.py": 0, "main.py": 2, "routers.py": 0}'}}
		resp = (await client.post(f'http://localhost/api/encrypt', params={'action': 'encrypt'}, files={'project_uuid': '0f617dc0-b4c0-4301-833e-b497ecfc4abb', 'files_to_encrypt': '{"config.py":0,"main.py":2,"routers.py":0}'})).json()
	print(resp)

asyncio.run(test())
import requests

headers = {
    'Accept-Language': 'ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7',
    'Connection': 'keep-alive',
    'Origin': 'http://localhost',
    'Referer': 'http://localhost/docs',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
    'accept': 'application/json',
    'sec-ch-ua': '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

params = {
    'action': 'encrypt',
}

files = {
    'project_uuid': (None, '0f617dc0-b4c0-4301-833e-b497ecfc4abb'),
    'files_to_encrypt': (None, '{"config.py":0,"main.py":2,"routers.py":0}'),
    'project_file': ('Spamboost.zip', '', 'application/x-zip-compressed')
}

req = requests.post('http://localhost/api/encrypt', params=params, headers=headers, files=files)
print(req)
print(req.json())