base:
    'vault':
        - vault.server

    'vault-master':
        - vault.masterless

    'web':
        - vault.client
        - boss.django

    'jenkins-master*':
        - git
        - python.python3
        - python.pip3
# Install 2.7.x pip so Salt's pip module can run.
        - python.pip
        - jenkins
        - jenkins.plugins
        - jenkins.slack
        - jenkins.jobs
# tox is probably unnecessary if we only target a single Python version.
# - python.tox
        - python.nose2-3
        - python.nose2-cov-3
