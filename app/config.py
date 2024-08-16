from pydantic import BaseModel

class Database(BaseModel):
	user: str = None
	password: str = None
	database: str = None
	host: str = None
	port: int = None

class Settings(BaseModel):
	database: Database
	default_salt: str
	website_url: str





settings = Settings(
	database=Database(
		user='neondb_owner',
		password='3h2WSfPTdIDk',
		database='neondb',
		host='ep-wispy-wind-a2usxind.eu-central-1.aws.neon.tech',
		port=5432
	),
	default_salt='C7JO-z2qkb1qoLfkuxmyZJ4q7OqdFucPyYY2YSvVvZc=',
	website_url='http://localhost'
)