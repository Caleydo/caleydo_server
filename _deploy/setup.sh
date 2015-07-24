#!/usr/bin/env bash

function sedeasy {
  sed "s/$(echo $1 | sed -e 's/\([[\/.*]\|\]\)/\\&/g')/$(echo $2 | sed -e 's/[\/&]/\\&/g')/g" $3 > $4
}

function install_apt_dependencies {
  if [ -f debian.txt ] ; then
    echo "--- installing apt dependencies ---"
    wd="`pwd`"
    cd /tmp #switch to tmp directory
    set -vx #to turn echoing on and
    sudo apt-get install -y supervisor python-pip python-dev zlib1g-dev `cat ${wd}/debian.txt`
    set +vx #to turn them both off
    cd ${wd}
    rm debian.txt
  fi
}
function install_pip_dependencies {
  if [ -f requirements.txt ] ; then
    echo "--- installing pip dependencies ---"
    wd="`pwd`"
    cd /tmp #switch to tmp directory
    pip install -r ${wd}/requirements.txt
    set -vx #to turn echoing on and
    cd ${wd}
    rm requirements.txt
  fi
}

function create_server_config {
  local name=$1
  wd="`pwd`"
  cd /tmp #switch to tmp directory
  pip install gunicorn setproctitle
  set -vx #to turn echoing on and
  cd ${wd}

  sedeasy caleydo_web $1 gunicorn_start.in.sh gunicorn_start.sh
  chmod +x gunicorn_start.sh

  sedeasy caleydo_web $1 supervisor.in.conf supervisor.conf
  #create the supervisor config
  sudo ln -s ${wd}/supervisor.conf /etc/supervisor/conf.d/${name}.conf

  #create the nginx config and enable the site
  if [ -d /etc/nginx ] ; then
    sedeasy caleydo_web $1 nginx.in.conf nginx.conf
    sudo ln -s ${wd}/nginx.conf /etc/nginx/sites-available/${name}
    sudo ln -s ${wd}/nginx.conf /etc/nginx/sites-enabled/${name}
  fi
}

function create_virtualenv {
  echo "--- creating virtual environment ---"
  wd="`pwd`"
  if hash virtualenv 2>/dev/null; then
     echo "virtualenv already installed"
  else
    sudo pip install virtualenv
  fi
  virtualenv venv
  source venv/bin/activate
}

function deactivate_virtualenv {
  deactivate
}

function create_run_script {
    echo "#!/usr/bin/env bash

./venv/bin/python plugins/caleydo_server --multithreaded
" > run.sh
}

install_apt_dependencies
create_virtualenv
install_pip_dependencies
create_run_script

name=${PWD##*/}
create_server_config ${name}

deactivate_virtualenv