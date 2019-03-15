#! python3

import subprocess
import venv
import os


def main():
    PRE = '\n[deliver.ai] --> '
    APP_PATH = os.path.dirname(os.path.abspath(__file__))
    VENV_PATH = os.path.join(APP_PATH, 'v   env')

    print(" --- ##   deliver.ai web app intaller   ## --- ")

    # create the virtual enviroment
    print(PRE + "Creating the virtual enviroment...")

    class ExtendedEnvBuilder(venv.EnvBuilder):
        def post_setup(self, context):
            os.environ['VIRTUAL_ENV'] = context.bin_path
            super().post_setup(context)

    v = ExtendedEnvBuilder(with_pip=True)
    v.create(VENV_PATH)

    path = os.getenv('VIRTUAL_ENV', None)
    if not path:
        raise Exception("Could not create virtual environment!")

    print(PRE + "Virtual environment created at: {}".format(APP_PATH))

    py_path = os.path.join(path, 'python')

    # upgrade pip
    print(PRE + "Upgrading pip:")
    subprocess.run([py_path, '-m', 'pip', 'install', '--upgrade', 'pip'])

    # install using pip (https://stackoverflow.com/a/15950647/9184658)
    req = 'requirements.txt'
    print(PRE + "Installing dependencies from file: {}".format(req))
    subprocess.run([py_path, '-m', 'pip', 'install', '-r', req])

    print(PRE + "Install successful!")


if __name__ == "__main__":
    main()
