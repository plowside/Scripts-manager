

from cryptography.fernet import Fernet
import subprocess, platform, uuid

cipher = Fernet(b'C7JO-z2qkb1qoLfkuxmyZJ4q7OqdFucPyYY2YSvVvZc=')

def get_machine_id():
	system = platform.system()
	try:
		machine_id = None
		if system == 'Linux': machine_id = subprocess.check_output(['sudo', 'cat', '/sys/class/dmi/id/product_uuid']).decode().strip()
		elif system == 'Windows':
			machine_id = subprocess.check_output('wmic csproduct get uuid').decode().split('\n')[1].strip()
	except: ...
	return machine_id

hwid = f'{uuid.getnode()}:{get_machine_id()}'
encrypted_text = cipher.encrypt(hwid.encode()).decode()
print(encrypted_text)




import asyncio
import base64
from cryptography.fernet import Fernet

key = b'C7JO-z2qkb1qoLfkuxmyZJ4q7OqdFucPyYY2YSvVvZc='
cipher = Fernet(key)

async def async_encrypt(plain_text):
    encrypted_text = await asyncio.get_running_loop().run_in_executor(None, cipher.encrypt, plain_text.encode())
    return encrypted_text.decode()

async def async_decrypt(encrypted_text):
    decrypted_text = await asyncio.get_running_loop().run_in_executor(None, cipher.decrypt, encrypted_text.encode())
    return decrypted_text.decode()

async def main():
    plain_text = "Your secret message"
    encrypted_text = await async_encrypt(plain_text)
    print(f"Encrypted Text: {encrypted_text}")

    decrypted_text = await async_decrypt(encrypted_text)
    print(f"Decrypted Text: {decrypted_text}")

asyncio.run(main())
