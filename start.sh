#!/bin/sh


create_env() {
    echo "[ENV FILE] creating .env file..."
    # check if file exists
    if [ -f "/var/interlegis/sapl/data/secret.key" ]; then
        KEY=`cat /var/interlegis/sapl/data/secret.key`
    else
        KEY=`python3 genkey.py`
        echo $KEY > data/secret.key
    fi

    FILENAME="/var/interlegis/sapl/sapl/.env"

    if [ -z "${DATABASE_URL:-}" ]; then
        DATABASE_URL="postgresql://sapl:sapl@sapldb:5432/sapl"
    fi

    # ALWAYS replace the content of .env variable
    # If want to conditionally create only if absent then use IF below
    #    if [ ! -f $FILENAME ]; then

    touch $FILENAME


    # explicitly use '>' to erase any previous content
    echo "SECRET_KEY="$KEY > $FILENAME
    # now only appends
    echo "DATABASE_URL = "$DATABASE_URL >> $FILENAME
    echo "DEBUG = ""${DEBUG-False}" >> $FILENAME
    echo "EMAIL_USE_TLS = ""${USE_TLS-True}" >> $FILENAME
    echo "EMAIL_PORT = ""${EMAIL_PORT-587}" >> $FILENAME
    echo "EMAIL_HOST = ""${EMAIL_HOST-''}" >> $FILENAME
    echo "EMAIL_HOST_USER = ""${EMAIL_HOST_USER-''}" >> $FILENAME
    echo "EMAIL_HOST_PASSWORD = ""${EMAIL_HOST_PASSWORD-''}" >> $FILENAME

    echo "[ENV FILE] done."
}

create_env

# # python3 gen-env.py

python3 manage.py bower install

/bin/sh busy-wait.sh $DATABASE_URL

python3 manage.py migrate
python3 manage.py collectstatic --no-input
python3 manage.py rebuild_index --noinput

user_created=$(python3 create_admin.py)

echo $user_created

#if [ $user_created -eq "ADMIN_USER_EXISTS" ]; then
#    echo "[SUPERUSER CREATION] User admin already exists. Not creating"
#fi

#if [ $user_created -eq "MISSING_ADMIN_PASSWORD" ]; then
#   echo "[SUPERUSER] Environment variable $ADMIN_PASSWORD for superuser admin was not set. Leaving container"
   # return -1 # TODO: Uncomment when in finally in prod.
#fi


/bin/sh gunicorn_start.sh no-venv
