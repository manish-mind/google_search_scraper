from decouple import config

DB_INSTANCE_HOST = config("DB_INSTANCE_HOST", default="localhost")
DB_NAME = config("DB_NAME", default="search_result")
DB_USER = config("DB_USER", default="postgres")
DB_PASSWORD = config("DB_PASSWORD", default="mind")
DB_PORT = config("DB_PORT", default="5432")


AWS_ACCESS_KEY_ID= config("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY= config("AWS_SECRET_ACCESS_KEY", default="")
AWS_REGION = config("AWS_REGION", default="")
AWS_S3_BUCKET_NAME= config("AWS_S3_BUCKET_NAME", default="")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_INSTANCE_HOST}:{DB_PORT}/{DB_NAME}"
