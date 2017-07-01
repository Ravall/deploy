# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from contextlib import contextmanager
from fabric.api import env, task, run, cd, prefix, get
from fabric.colors import green
from fabric.contrib.files import append, upload_template
from functools import wraps
from config import ENV
from pathlib import Path

try:
    from StringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO


class FabException(Exception):
    pass


def log_call(func):
    @wraps(func)
    def logged(*args, **kawrgs):
        header = "-" * len(func.__name__)
        print("Executing on %s as %s" % (env.host, env.user))
        print(green("\n".join([header, func.__name__, header]), bold=True))
        print()
        return func(*args, **kawrgs)
    return logged


@contextmanager
def virtualenv():
    """
    Runs commands within the project's virtualenv.
    """
    with prefix("source {0}/{1}/bin/activate".format(
            PROJECT_ENV['VIRTUALENV_HOME'], PROJECT_ENV.get("VIRTUALENV_NAME", PROJECT_ENV['PROJECT_NAME'])
    )):
        yield


@contextmanager
def project():
    """
    Runs commands within the project's directory.
    """
    with cd(get_project_path()):
        yield


def pip(packages):
    """
    Installs one or more Python packages within the virtual environment.
    """
    with virtualenv():
        run("pip install --allow-all-external %s " % packages)



def is_operation_complete(project, operation):
    """
    проверяет есть ли операция в лог файле
    :param project:
    :param operation:
    :return:
    """
    with cd(''):
        fd = StringIO()
        get('{}.txt'.format(project), fd)
        content = fd.getvalue().split()
    return operation in [x.decode("utf-8") for x in content]


def set_operation_complete(project, operation):
    with cd(''):
        append('{}.txt'.format(project), operation)


def server_operation(fn):
    @wraps(fn)
    def wrapper(*args, **kawrgs):
        if not is_operation_complete(PROJECT_ENV['PROJECT_NAME'], fn.__name__):
            fn(*args, **kawrgs)
            set_operation_complete(PROJECT_ENV['PROJECT_NAME'], fn.__name__)
        else:
            print("{} is complete".format(fn.__name__))
    return wrapper


def get_project_path():
    return '{home}/{name}'.format(
        home=PROJECT_ENV['HOME'], name=PROJECT_ENV['PROJECT_NAME']
    )


@server_operation
def mk_project():
    run("mkdir -p {}" .format(get_project_path()))


@server_operation
def git_checkout():
    with cd(get_project_path()):
        run('git clone {git_url} .'.format(git_url=PROJECT_ENV['GIT_URL']))
        run('git submodule init')
        run('git submodule update')


@server_operation
def mk_virtualenv():
    if not PROJECT_ENV.get('IS_VIRTUALENV', True):
        return
    with cd(PROJECT_ENV['VIRTUALENV_HOME']):
        run('virtualenv {add_params} {project_name}'.format(
            add_params=PROJECT_ENV['MK_VIRTUALENV_PARAMS'],
            project_name=PROJECT_ENV['PROJECT_NAME']
        ))


@server_operation
def pip_install():
    if not PROJECT_ENV.get('IS_VIRTUALENV', True):
        return
    with project():
        pip("-r {}".format(PROJECT_ENV['REQUIREMENTS_FILE']))


def sql_query(sql, db_login, db_passwod):
    run('echo "{0};" | mysql -u{login} -p{pwd}'.format(sql,login=db_login, pwd=db_passwod))


def sql_root_query(sql):
    return sql_query(sql, 'root', PROJECT_ENV['DATABASE']['root_pass'])


@server_operation
def mk_database():
    if not PROJECT_ENV.get('IS_DATABASE', True):
        return
    sql_root_query("CREATE DATABASE IF NOT EXISTS {}".format(PROJECT_ENV['DATABASE']['name']))
    sql_root_query("CREATE USER '{user}'@'localhost' IDENTIFIED BY '{password}';".format(
        user=PROJECT_ENV['DATABASE']['user'],
        password=PROJECT_ENV['DATABASE']['password'])
    )
    sql_root_query("GRANT ALL PRIVILEGES ON {db_name}.* TO '{user}'@'localhost'".format(
        db_name = PROJECT_ENV['DATABASE']['name'],
        user=PROJECT_ENV['DATABASE']['user']
    ))
    sql_root_query("FLUSH PRIVILEGES")


@server_operation
def project_database_config():
    if not PROJECT_ENV.get('IS_DATABASE', True):
        return
    context = {
        'db_name': PROJECT_ENV['DATABASE']['name'],
        'db_user': PROJECT_ENV['DATABASE']['user'],
        'db_user_password': PROJECT_ENV['DATABASE']['password']
    }
    upload_template(
        'template/production.tpl',
        '{0}/{1}/production.py'.format(get_project_path(), PROJECT_ENV['settings_path']),
        context=context,
        use_sudo=True
    )


def manage_py(cmd):
    run('python {path}/manage.py {cmd}'.format(
        path=PROJECT_ENV['manage_py_path'], cmd=cmd
    ))


@server_operation
def prepare_django_project():
    if not PROJECT_ENV.get('IS_VIRTUALENV', True):
        return
    with virtualenv():
        with project():
            manage_py('collectstatic --noinput')
            manage_py('syncdb --noinput')
            manage_py('migrate --noinput')
            run('echo "from django.contrib.auth.models import User;'
                ' User.objects.create_superuser(\'{admin_login}\', \'{admin_email}\', \'{admin_password}\')" '
                '| python {path}/manage.py shell'.format(
                admin_login=PROJECT_ENV['admin']['login'],
                admin_email=PROJECT_ENV['admin']['email'],
                admin_password=PROJECT_ENV['admin']['password'],
                path=PROJECT_ENV['manage_py_path']
            ))


@server_operation
def nginx_config():
    context = {
        'proj_name': PROJECT_ENV['PROJECT_NAME'],
        'static_path': '{project_path}/{static_path}'.format(
            project_path=get_project_path(),
            static_path=PROJECT_ENV['static_path']
        ),
        'port': PROJECT_ENV['PORT'],
        'proj_path': get_project_path(),
    }

    upload_template(
        'template/nginx.{}.tpl'.format(PROJECT_ENV['PROJECT_NAME']),
        '/etc/nginx/sites-enabled/{}'.format(PROJECT_ENV['PROJECT_NAME']),
        context=context,
        use_sudo=True
    )
    config_file = 'template/upstream.{}.tpl'.format(PROJECT_ENV['PROJECT_NAME'])
    if Path(config_file).is_file():
        upload_template(
            config_file,
            '/etc/nginx/conf.d/{}.upstream.conf'.format(PROJECT_ENV['PROJECT_NAME']),
            context=context,
            use_sudo=True
        )


@server_operation
def supervisor_config():
    if not PROJECT_ENV.get('IS_VIRTUALENV', True):
        return
    context = {
        'proj_name': PROJECT_ENV['PROJECT_NAME'],
        'envs_path': PROJECT_ENV['VIRTUALENV_HOME'],
        'proj_path': get_project_path(),
        'manage_py_path': PROJECT_ENV['manage_py_path'],
        'port': PROJECT_ENV['PORT']
    }
    upload_template(
        'template/supervisor.tpl',
        '/etc/supervisor/conf.d/{}.conf'.format(PROJECT_ENV['PROJECT_NAME']),
        context=context,
        use_sudo=True
    )


def service_restart():
    run('service nginx restart')
    run('service supervisor restart')


def get_ENV(project):
    PROJECT_ENV = ENV.get(project, False)
    if not PROJECT_ENV:
        raise FabException('unknown env')
    global PROJECT_ENV


@task
@log_call
def create_project(project):
    """
    fab create_project:project --host=root@ip
    :param project:
    :return:
    """
    try:
        get_ENV(project)
        """
        последователность действий
        """
        mk_project()
        git_checkout()
        mk_virtualenv()
        pip_install()
        mk_database()
        project_database_config()
        prepare_django_project()
        nginx_config()
        supervisor_config()
        service_restart()
    except FabException as e:
        print(str(e))
        exit()

@task
@log_call
def update_project(project):
    """
       fab create_project:project --host=root@ip
       :param project:
       :return:
       """

    try:
        get_ENV(project)
        """
        последователность действий
        """
        nginx_config()
        supervisor_config()
        service_restart()
    except FabException as e:
        print(str(e))
        exit()

@task
@log_call
def deploy(prj):
    try:
        get_ENV(prj)

        with project():
            run("git pull origin master")
            if PROJECT_ENV.get('IS_VIRTUALENV', True):
                pip("-r {}".format(PROJECT_ENV['REQUIREMENTS_FILE']))
        if PROJECT_ENV.get('IS_VIRTUALENV', True):
            with virtualenv():
                with project():
                    manage_py("collectstatic -v 0 --noinput")
                    manage_py("migrate --noinput")

        service_restart()
    except FabException as e:
        print(str(e))
        exit()
