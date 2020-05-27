#!/bin/bash
python3 manage.py makemigrations orders
python3 manage.py makemigrations users
python3 manage.py migrate orders
python3 manage.py migrate users
python3 manage.py migrate
res="$?"
while [ "$res" != "0" ]
do
    sleep 3;
    python3 manage.py migrate
    res="$?"
done

