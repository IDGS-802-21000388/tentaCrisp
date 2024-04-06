class Config(object):
    SECRET_KEY = 'CLAVE SECRETA'
    SESSION_COOKIE_SECURE=False

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://EdwinRivera:Yovani2002@127.0.0.1/don_galletoV2'
    CORS_ORIGINS = ['http://localhost:']
    # RECAPTCHA_USE_SSL = False
    # RECAPTCHA_PUBLIC_KEY = "6Ld-ZZ0pAAAAAHAoFh6fPuhpGmck_IeSrK6SRcyR"
    # RECAPTCHA_PRIVATE_KEY = "6Ld-ZZ0pAAAAAD5Cdnk8FM1v4S6NEx0-9-vkrBhZ"
    # RECAPTCHA_OPTIONS = {'theme': 'black'}