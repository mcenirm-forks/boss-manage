nodesource-repo:
  pkgrepo.managed:
    - humanname: nodesource
    - name: deb https://deb.nodesource.com/node_5.x trusty main
    - file: /etc/apt/sources.list.d/nodesource.list
    - key_url: salt://proofreader-web/files/nodesource.gpg.key

nodejs:
  pkg.installed:
    - fromrepo: trusty

npm@3.7.5:
  npm.installed:
    - require:
      - pkg: nodejs

bower@1.7.7:
  npm.installed:
    - require:
      - pkg: nodejs

gulp@3.9.1:
  npm.installed:
    - require:
      - pkg: nodejs
