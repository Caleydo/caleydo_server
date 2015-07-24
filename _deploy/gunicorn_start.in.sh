#!/bin/bash

NAME="caleydo_app"                                  # Name of the application
WEB_DIR=/var/www/caleydo_app             # Django project directory
SOCKFILE=/var/www/caleydo_app/run/gunicorn.sock  # we will communicte using this unix socket
USER=ubuntu                                        # the user to run as
GROUP=data-www                                     # the group to run as
NUM_WORKERS=3                                     # how many worker processes should Gunicorn spawn
CALEYDO_WSGI_MODULE=plugins.caleydo_server.__main__                     # WSGI module name

echo "Starting $NAME as `whoami`"

# Activate the virtual environment
cd ${WEB_DIR}
source ./venv/bin/activate
export PYTHONPATH=${WEB_DIR}:${PYTHONPATH}

# Create the run directory if it doesn't exist
RUNDIR=$(dirname ${SOCKFILE})
test -d ${RUNDIR} || mkdir -p ${RUNDIR}

# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
exec ./venv/bin/gunicorn ${CALEYDO_WSGI_MODULE}:application \
  -k flask_sockets.worker \
  --name ${NAME} \
  --workers ${NUM_WORKERS} \
  --user=${USER} --group=${GROUP} \
  --bind=unix:${SOCKFILE} \
  --log-level=debug \
  --log-file=-