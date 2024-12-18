
release: python manage.py collectstatic --noinput
web: gunicorn Fin_v2_by.wsgi:application --bind 0.0.0.0:$PORT --timeout 120
