export STATIC_DIR="${PWD}/static"
# NOTE: Data dir should be somewhere insde static dir (as the server serve data as static files)
export DATA_DIR="${STATIC_DIR}/data"
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"
export LOGS_DIR="${PWD}/logs"