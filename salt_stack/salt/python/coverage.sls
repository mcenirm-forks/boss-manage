# This is a Python 3.5 specific formula.
include:
    - python.python35
    - python.pip

coverage:
    pip.installed:
        - name: coverage==4.0.3
        - bin_env: /usr/local/bin/pip3
        - require:
            - sls: python.python35
            - sls: python.pip
