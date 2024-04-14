import secrets
from cryptography.fernet import Fernet
clave = Fernet.generate_key()

def encriptar_cadena(cadena_conexion, clave):
    cipher_suite = Fernet(clave)
    # Desencripta la cadena de conexión
    cadena_encriptada = cipher_suite.encrypt(cadena_conexion.encode())
    return cadena_encriptada.decode()

cadena_encriptada = encriptar_cadena(
    'mysql+pymysql://EdwinRivera:Yovani2002@127.0.0.1/don_galletoV2', 
    clave
)

def desencriptar_cadena_conexion(cadena_encriptada, clave):
    cipher_suite = Fernet(clave)
    cadena_desencriptada = cipher_suite.decrypt(cadena_encriptada.encode())
    return cadena_desencriptada.decode()

class Config(object):
    SECRET_KEY = 'CLAVE SECRETA'
    SESSION_COOKIE_SECURE=False

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = desencriptar_cadena_conexion(cadena_encriptada, clave)
    CORS_ORIGINS = ['http://localhost:']
    # RECAPTCHA_USE_SSL = False
    # RECAPTCHA_PUBLIC_KEY = "6Ld-ZZ0pAAAAAHAoFh6fPuhpGmck_IeSrK6SRcyR"
    # RECAPTCHA_PRIVATE_KEY = "6Ld-ZZ0pAAAAAD5Cdnk8FM1v4S6NEx0-9-vkrBhZ"
    # RECAPTCHA_OPTIONS = {'theme': 'black'}