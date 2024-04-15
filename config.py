import base64

def encrypt(cadena):
    return base64.b64encode(cadena.encode()).decode()
def decrypt(cadena_ofuscada):
    return base64.b64decode(cadena_ofuscada.encode()).decode()

cadena_conexion = 'mysql+pymysql://EdwinRivera:Yovani2002@127.0.0.1/don_galletoV2'

cadena_ofuscada = encrypt(cadena_conexion)
cadena_descifrada = decrypt(cadena_ofuscada)

class Config(object):
    SECRET_KEY = 'CLAVE SECRETA'
    SESSION_COOKIE_SECURE=False

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = decrypt(cadena_ofuscada)
    CORS_ORIGINS = ['http://localhost:']
    # RECAPTCHA_USE_SSL = False
    # RECAPTCHA_PUBLIC_KEY = "6Ld-ZZ0pAAAAAHAoFh6fPuhpGmck_IeSrK6SRcyR"
    # RECAPTCHA_PRIVATE_KEY = "6Ld-ZZ0pAAAAAD5Cdnk8FM1v4S6NEx0-9-vkrBhZ"
    # RECAPTCHA_OPTIONS = {'theme': 'black'}