#! python3

import subprocess
import venv
import os


def main():
    PRE = '\n[deliver.ai] --> '

    print(" --- ##   deliver.ai web app intaller   ## --- ")

    # # create the virtual enviroment
    print(PRE + "Creating the virtual enviroment...")

    class ExtendedEnvBuilder(venv.EnvBuilder):
        def post_setup(self, context):
            os.environ['VIRTUAL_ENV'] = context.bin_path
            super().post_setup(context)

    v = ExtendedEnvBuilder(with_pip=True)
    v.create('venv')

    path = os.getenv('VIRTUAL_ENV', None)
    if not path:
        raise Exception("Could not create virtual environment!")

    print(PRE + "Virtual environment created at: {}".format(path))

    py_path = os.path.join(path, 'python')

    # upgrade pip
    print(PRE + "Upgrading pip:")
    upgrade_pip = subprocess.run(
        [py_path, '-m', 'pip', 'install', '--upgrade', 'pip'])

    # install using pip (https://stackoverflow.com/questions/12332975/installing-python-module-within-code)
    req = 'requirements.txt'
    print(PRE + "Installing dependencies from file: {}".format(req))
    install_req = subprocess.run([py_path, '-m', 'pip', 'install', '-r', req])

    print(PRE + "Install successful!")


if __name__ == "__main__":
    main()
