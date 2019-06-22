import subprocess
import venv
import os


def main():
    MSG = '[deliver.ai] --> {}\n'
    APP_PATH = os.path.dirname(os.path.abspath(__file__))
    os.chdir(APP_PATH)
    VENV_PATH = os.path.join(APP_PATH, 'venv')

    print("\n --- ##   deliver.ai web app installer   ## --- \n")

    # create the virtual environment
    print(MSG.format("Creating the virtual environment..."))

    class ExtendedEnvBuilder(venv.EnvBuilder):
        def post_setup(self, context):
            os.environ['VIRTUAL_ENV'] = context.bin_path
            super().post_setup(context)

    v = ExtendedEnvBuilder(with_pip=True)
    v.create(VENV_PATH)

    path = os.getenv('VIRTUAL_ENV', None)
    if not path:
        raise Exception("Could not create virtual environment!")

    print(MSG.format("Virtual environment created at: {}".format(APP_PATH)))

    py_path = os.path.join(path, 'python')
    with open('path.py', 'w') as f:
        f.writelines('\n'.join([
            'py_path = {}'.format(py_path.encode()),
            'app_path = {}'.format(APP_PATH.encode()),
            '',
        ]))

    # upgrade pip
    print(MSG.format("Upgrading pip:"))
    subprocess.run([py_path, '-m', 'pip', 'install', '--upgrade', 'pip'])

    # install using pip (https://stackoverflow.com/a/15950647/9184658)
    req = 'requirements.txt'
    print(MSG.format("Installing dependencies from file: {}".format(req)))
    subprocess.run([py_path, '-m', 'pip', 'install', '-r', req])

    print(MSG.format("Install successful!"))


if __name__ == "__main__":
    main()
