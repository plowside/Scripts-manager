import asyncio, httpx

async def test():
	async with httpx.AsyncClient() as client:
		file_resp = await client.get('https://api.telegram.org/file/bot7306244866:AAG8kB3Uwhx71sxJ-FrhgLBDTBNQd2eeYWI/documents/file_1.zip')
		resp = (await client.post('http://localhost/api/encrypt', params={'action': 'upload_zip', 'project_uuid': 'c5bc9859-0504-4d65-9c9e-05833d6f8831'}, files={'project_file': file_resp.content})).json()
	print(resp)

asyncio.run(test())