
ENV = {
    'engdel.ru': {
        'HOME': '/home/www',
        'VIRTUALENV_HOME': '/home/envs',
        'MK_VIRTUALENV_PARAMS': '',
        'PROJECT_NAME': 'engdel.ru',
        'PROJECT_SHORT_NAME': 'engdel',
        'GIT_URL': 'git@github.com:Ravall/foreign.git',
        'REQUIREMENTS_FILE': 'pip.freeze',
        'DATABASE': {
            'name': 'engdel_db',
            'user': 'engdel_user',
            'password': '',
            'root_pass': ''
        },
        'PORT': 8009,
        'settings_path': 'frgn/frgn',
        'manage_py_path': 'frgn',
        'static_path': 'files/collected_static',
        'admin': {
            'login': '',
            'email': '',
            'password': ''
        },
    },
    'geodiscover.org': {
        'HOME': '/home/www',
        'PROJECT_NAME': 'geodiscover.org',
        'GIT_URL': 'git@bitbucket.org:ravall/boars_project.git',
        'IS_VIRTUALENV': False,
        'IS_DATABASE': False,
        'static_path': '/home/www',
        'PORT': '',
        'MK_VIRTUALENV_PARAMS': '',
    },
    'api': {
        'HOME': '/home/www',
        'VIRTUALENV_HOME': '/home/envs',
        'VIRTUALENV_NAME': 'mezzanine3',
        'PROJECT_NAME': 'content_api',
        'GIT_URL': 'git@bitbucket.org/boarshightentropy/mezzanine3.git',
        'REQUIREMENTS_FILE': 'requirements.txt',
        'settings_path': 'cms/cms',
        'manage_py_path': 'cms',
    }
}