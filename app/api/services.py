import datetime, secrets, string, time

from cryptography.fernet import Fernet

from .models import *
from ..database import *




async def ts():
	return int(time.time())

async def gen_key(length = 32):
	return ''.join(secrets.choice(string.ascii_lowercase, k=length)).upper()

async def gen_name():
	return ''.join(secrets.choice(string.ascii_lowercase, k=16))



class Project:
	@staticmethod
	async def create(name: str = None):
		try:
			if name:
				get_project = await Project.get(name=name)
				if get_project:
					name = await gen_name()
			else:
				name = await gen_name()
			this_ts = await ts()
			salt = Project.gen_salt()
			await db.execute('INSERT INTO project(name, salt, create_ts) VALUES ($1, $2, $3)', name, salt, this_ts)
			return await Project.get(name=name)
		except Exception as e:
			raise e

	@staticmethod
	async def get(id: int = None, name: str = None):
		try:
			if id or name:
				get_project = await db.fetchrow('SELECT * FROM project WHERE id = $1 OR name = $2', id, name)
				if get_project:
					return db.Project(**get_project)
			return None
		except Exception as e:
			raise e

	@staticmethod
	async def update(id: int, name: str):
		try:
			await db.execute('UPDATE project SET name = $1 WHERE id = $2', name, id)
			return True
		except Exception as e:
			raise e


	@staticmethod
	async def gen_salt():
		generated_salt = await asyncio.get_running_loop().run_in_executor(None, Fernet.generate_key)
		return generated_salt.decode()





class LicenseKey:
	@staticmethod
	async def create(project_id: int, exp_ts: int = None, timedelta: datetime.timedelta = None):
		try:
			get_project = await Project.get(id=project_id)
			if not get_project:
				return False

			value = await gen_key()
			this_ts = await ts()

			if timedelta:
				exp_ts = (datetime.datetime.fromtimestamp(this_ts) + timedelta).timestamp()
			
			await db.execute('INSERT INTO license_key(project_id, value, exp_ts, create_ts) VALUES ($1, $2, $3, $4)', get_project.id, value, exp_ts, this_ts)
			return await LicenseKey.get(value=value)
		except Exception as e:
			raise e

	@staticmethod
	async def get(project_id: int = None, id: int = None, value: str = None):
		try:
			if project_id:
				return await db.fetch('SELECT * FROM license_key WHERE project_id = $1', project_id)
			elif id or value:
				get_license_key = await db.fetchrow('SELECT * FROM license_key WHERE id = $1 OR value = $2', id, value)
				if get_license_key:
					return db.LicenseKey(**get_license_key)
			return None
		except Exception as e:
			raise e

	@staticmethod
	async def update(id: int, exp_ts: int):
		try:
			await db.execute('UPDATE license_key SET exp_ts = $1 WHERE id = $2', exp_ts, id)
			return True
		except Exception as e:
			raise e

	@staticmethod
	async def activate(license_key_id: int, mac: str, hwid: str = None):
		try:
			await db.execute('INSERT INTO license_key_connections(license_key_id, mac, hwid, create_ts) VALUES ($1, $2, $3, $4)', license_key_id, mac, hwid, await ts())
			return True
		except Exception as e:
			raise e

	@staticmethod
	async def verify(license_key: db.LicenseKey, mac: str, hwid: str = None):
		try:
			async with db.pool.acquire() as conn:
				license_key_connections = await conn.fetch('SELECT * FROM license_key_connections WHERE license_key_id = $1', license_key.id)
				valid = len() > 0
				if valid:
					get_connection = await conn.fetchrow('SELECT * FROM license_key_connections WHERE license_key_id = $1', license_key.id)
					return (True, mac, hwid)
				elif not valid and len(license_key_connections) < license_key.max_connections:
					activated = await LicenseKey.activate()
					get_connection = await conn.fetchrow('SELECT * FROM license_key_connections WHERE license_key_id = $1', license_key.id)
					return (True, mac, hwid)
				elif not valid and len(license_key_connections) >= license_key.max_connections:
					return (False, 'too_many_connections', 'Достигнуто максимальное количество подключений')
				else:
					return (False, 'unknown_error', 'Неизвестная ошибка')

			return None
		except Exception as e:
			raise e

	
	@staticmethod
	async def decrypt(encrypted_payload, key):
		decrypted_text = await asyncio.get_running_loop().run_in_executor(None, Fernet(key).decrypt, encrypted_payload.encode())
		return decrypted_text.decode()

	@staticmethod
	async def encrypt(plain_payload, key):
		encrypted_text = await asyncio.get_running_loop().run_in_executor(None, Fernet(key).encrypt, plain_payload.encode())
		return encrypted_text.decode()