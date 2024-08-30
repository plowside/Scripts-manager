import subprocess, warnings, platform, asyncio, time, uuid, sys, os

warnings.simplefilter('ignore', RuntimeWarning)
try:
	from cryptography.fernet import Fernet
	import requests, httpx
except ImportError:
	subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography requests httpx"])
	from cryptography.fernet import Fernet
	import requests, httpx


try: website_url = requests.get('https://raw.githubusercontent.com/plowside/plowside/main/assets/info.json').json()['scmwu']
except: website_url = 'here_website_url'

def check(key, _exit = False):
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
	hwid = f'{this_project_uuid}:{key}:{this_mac}:{this_hwid}'
	encrypted_text = cipher.encrypt(hwid.encode()).decode()
	req = requests.post(f'{website_url}/api/license_key', json={'action': 'check', 'key': encrypted_text})
	resp = req.json()
	if resp['error']:
		if _exit:
			exit(resp['error_desc'])
			while True: input()
		return (False, None)
	try:
		cipher = Fernet('here_fernet_project_key')
		decrypted_text = cipher.decrypt(resp['pyarmor_key'].encode()).decode()
	except:
		if _exit:
			exit('Недействительный ключ активации')
			while True: input()
		return (False, None)

	try:
		decrypted_text_parts = decrypted_text.split(':')
		project_uuid = '-'.join(decrypted_text_parts[0].split('-')[:-1])
		project_create_ts = float(decrypted_text_parts[0].split('-')[-1])
		license_key_id, license_key_create_ts = decrypted_text_parts[1].split('-')
		this_server_ts = float(decrypted_text_parts[2].split('-')[0])
		license_key_exp_ts = float(decrypted_text_parts[2].split('-')[1])
		this_connection_mac = decrypted_text_parts[3].split('-')[0]
		this_connection_hwid = '-'.join(decrypted_text_parts[3].split('-')[1:])
		this_connection_hwid = None if this_connection_hwid.lower() in ['', 'none', 'null'] else this_connection_hwid
	except:
		if _exit:
			exit('Просроченный ключ активации')
			while True: input()
		return (False, None)
	if this_server_ts >= license_key_exp_ts:
		if _exit:
			exit('Просроченный ключ активации')
			while True: input()
		return (False, None)
	elif this_connection_mac != this_mac or (False if (this_hwid == None or this_connection_hwid == None) else this_hwid != this_connection_hwid) or this_project_uuid != project_uuid:
		if _exit:
			exit('Недействительный ключ активации')
			while True: input()
		return (False, None)
	return (True, license_key_exp_ts)
if os.path.isfile('__'): _, license_key_exp_ts = check(open('__', encoding='utf-8').read().strip().upper())
else: _, license_key_exp_ts = (False, None)
if not os.path.isfile('__') or os.path.isfile('__') and not _:
	key = input('Введите ключ активации: ').strip().upper()
	_, license_key_exp_ts = check(key, True)
	open('__', 'w', encoding='utf-8').write(key)


async def license_watcher():
	while True:
		async with httpx.AsyncClient(timeout=180) as client:
			try:
				resp = await client.get(f'{website_url}/ts')
				server_ts = float(resp.text)
				if server_ts >= license_key_exp_ts:
					exit('Истёк срок действия ключа активации')
			except Exception as e: ...
			await asyncio.sleep(60)

__loop = asyncio.new_event_loop()
__loop.create_task(license_watcher())