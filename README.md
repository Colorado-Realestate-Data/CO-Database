A RESTful API written in Django for lookup of colorado property data


## Setting up
This project was built with python +3.4

```bash
$ virtualenv -p python3 env
$ source ./env/bin/activate
$ pip install -r requirements.txt
$ cd coprop
$ python manage.py migrate
$ python manage.py runserver
```

Then head to http://localhost:8000/api/v1/ in your browser to get started.
