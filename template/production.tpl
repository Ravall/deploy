DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': '%(db_name)s',
        'USER': '%(db_user)s',
        'PASSWORD': '%(db_user_password)s',
        'HOST': '127.0.0.1',
        'PORT': '',
    }
}