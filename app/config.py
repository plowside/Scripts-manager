from pydantic import BaseModel

class Database(BaseModel):
	user: str = None
	password: str = None
	database: str = None
	host: str = None
	port: int = None

class Settings(BaseModel):
	database: Database
	default_salt: bytes





settings = Settings(
	database=Database(
		user='postgres',
		password='plowside',
		database='test_license',
		host='localhost',
		port=5432
	),
	default_salt='C7JO-z2qkb1qoLfkuxmyZJ4q7OqdFucPyYY2YSvVvZc='.encode()
)
