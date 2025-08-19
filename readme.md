<p align="center">
    <a href="https://docs.djangoproject.com/es/5.1/topics/" target="_blank">
        <img src="https://www.djangoproject.com/m/img/logos/django-logo-negative.svg" width="400" alt="Laravel Logo">
    </a>
</p>
<h2 align="center">msentregables-notificaciones</h2>

### Versiones de tecnologías:

- [Python](https://www.python.org/downloads/release/python-3131/): 3.13
- [Django](https://docs.djangoproject.com/es/5.1/topics/install/): 5.1

#### Como iniciar microservicio en local

```shell
# Solo la primera vez
pip install -r requirements.txt

python manage.py migrate django_apscheduler
```

```shell
python manage.py start_scheduler
```
