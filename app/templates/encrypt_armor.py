from cryptography.fernet import Fernet
import subprocess, platform, requests, asyncio, httpx, time, uuid

cipher = Fernet('here_fernet_default_key')

def get_machine_id():
	system = platform.system()
	try:
		machine_id = None
		if system == 'Linux': machine_id = subprocess.check_output(['sudo', 'cat', '/sys/class/dmi/id/product_uuid']).decode().strip()
		elif system == 'Windows':
			machine_id = subprocess.check_output('wmic csproduct get uuid').decode().split('\n')[1].strip()
	except: ...
	return machine_id
this_mac = str(uuid.getnode())
this_hwid = get_machine_id()

this_project_uuid = 'here_project_uuid'
key = input('Введите ключ активации: ').strip().upper()
hwid = f'{this_project_uuid}:{key}:{this_mac}:{this_hwid}'
encrypted_text = cipher.encrypt(hwid.encode()).decode()
req = requests.post('here_website_url/api/license_key', json={'action': 'check', 'key': encrypted_text})
resp = req.json()
if resp['error']:
	exit(resp['error_desc'])
	while True: input()

try:
	cipher = Fernet('here_fernet_project_key')
	decrypted_text = cipher.decrypt(resp['pyarmor_key'].encode()).decode()
except:
	exit('Недействительный ключ активации')
	while True: input()
decrypted_text_parts = decrypted_text.split(':')
project_uuid = '-'.join(decrypted_text_parts[0].split('-')[:-1])
project_create_ts = float(decrypted_text_parts[0].split('-')[-1])
license_key_id, license_key_create_ts = decrypted_text_parts[1].split('-')
this_server_ts = float(decrypted_text_parts[2].split('-')[0])
license_key_exp_ts = float(decrypted_text_parts[2].split('-')[1])
this_connection_mac = decrypted_text_parts[3].split('-')[0]
this_connection_hwid = '-'.join(decrypted_text_parts[3].split('-')[1:])
this_connection_hwid = None if this_connection_hwid.lower() in ['', 'none', 'null'] else this_connection_hwid

if this_server_ts >= license_key_exp_ts:
	exit('Просроченный ключ активации')
	while True: input()
elif this_connection_mac != this_mac or (False if (this_hwid == None or this_connection_hwid == None) else this_hwid != this_connection_hwid) or this_project_uuid != project_uuid:
	exit('Недействительный ключ активации')
	while True: input()



async def license_watcher():
	while True:
		async with httpx.AsyncClient() as client:
			resp = await client.get('here_website_url/ts')
			server_ts = float(resp.text)
			if server_ts >= license_key_exp_ts:
				exit('Истёк срок действия ключа активации')
			await asyncio.sleep(60)

__loop = asyncio.new_event_loop()
__loop.create_task(license_watcher())