from decouple import config

DB_INSTANCE_HOST = config("DB_INSTANCE_HOST", default="localhost")
DB_NAME = config("DB_NAME", default="search_result")
DB_USER = config("DB_USER", default="postgres")
DB_PASSWORD = config("DB_PASSWORD", default="mind")
DB_PORT = config("DB_PORT", default="5432")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_INSTANCE_HOST}:{DB_PORT}/{DB_NAME}"
