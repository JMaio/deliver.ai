#! python3

import subprocess
import os
from flask_app.path import py_path


def main():
    MSG = '[deliver.ai] --> {}\n'

    wd = os.path.dirname(os.path.abspath(__file__))
    os.chdir(os.path.join(wd, 'flask_app'))

    print(MSG.format("Starting web app..."))
    subprocess.run(
        [py_path.decode(), '-m', 'flask', 'run', '--host', '0.0.0.0'])


if __name__ == "__main__":
    main()
