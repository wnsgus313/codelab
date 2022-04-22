import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in \
        ['true', 'on', '1']
    MAIL_USERNAME = 'testcase1019@gmail.com'
    MAIL_PASSWORD = 'hcyufmhhfmpqrmfe'
    FLASKY_MAIL_SUBJECT_PREFIX = '[Sign]'
    FLASKY_MAIL_SENDER = 'Sign Admin <sign@example.com>'
    FLASKY_ADMIN = 'jbm2627@gmail.com'# os.environ.get('FLASKY_ADMIN')
    FLASKY_USERS_PER_PAGE = 20
    FLASKY_COMMENTS_PER_PAGE = 30
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GOOGLE_OAUTH_CLIENT_ID = '812467256808-nb294uerji13f5nnbbgtvgj2huugrfr4.apps.googleusercontent.com' 
    GOOGLE_OAUTH_CLIENT_SECRET = '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'
    GOOGLE_DISCOVERY_URL = ("https://accounts.google.com/.well-known/openid-configuration")
    SSL_REDIRECT = False
    @staticmethod
    def init_app(app):
        pass
        
    
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite://'


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data.sqlite')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
