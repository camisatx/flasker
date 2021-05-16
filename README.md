# Flasker

🚨🚨 **Developmental software - use with caution!** 🚨🚨

A starting template for a Flask API backend. Components include user account functionality and a simple data retrieval example. Database connectivity is handled through SqlAlchemy, enabling the use of Postgres, MySQL, and Sqlite3.

## How to Use

### Clone Into Project

If you are using Flasker within another project, make a bare clone of this repository into a new folder called `api`. Starting at the root folder of your project, run:

`git clone https://github.com/camisatx/flasker.git api`

Since you will be modifying the Flasker files for your own project, it is best to disconnect it from the remote repository. Do this by removing the `.git` folder with:

`rm -rf .git/`

### Initialize Database

Make sure Postgres engine is running. You can use the Docker Postgres engine by running `docker-compose -f docker-compose-dev-locally.yml up postgres`, which will create the database and setup the correct user accounts based on the database settings specified in `docker-compose-dev-locally.yml`.

Initialize the database migration with `flask db init`.

Run a database migration with `flask db migrate -m "message"`.

Apply the changes to the database with `flask db upgrade`.

Run the application with `flask run`.

### Normal Application Start

#### With Docker

Change paths to the directory: `cd flasker`.

Make sure you have Docker ([Windows](https://docs.docker.com/docker-for-windows/install/); [Ubuntu](https://docs.docker.com/install/linux/docker-ce/ubuntu/)) and [docker-compose](https://docs.docker.com/compose/install/) installed.

##### Development Locally

Run `docker-compose -f docker-compose-dev-locally.yml up --build` to download and get the application running locally on port 5000.

##### Production

Run `docker-compose up --build` to download and get the application running through the lets-encrypt/nginx webproxy container on port 80.


#### Without Docker

Change paths to the directory: `cd flasker`

Activate your virtual environment: `virtualenv flasker`

Install requirements: `pip install -r requirements.txt`

Run `export FLASK_APP=flasker.py` to add the app to the flask environment.

### Updating the Database

Apply the changes to the database with `flask db upgrade`

Run the application with `flask run`

### Using RQ Tasks Server

If using the optional RQ task server, start the Redis container with `docker run -rm -p 6379:6379 redis`

Start an RQ worker with `rq worker flasker-tasks`

## Copyright

Copyright (c) 2021 Joshua Schertz

## License

Flasker is open source software [licensed as MIT](https://github.com/camisatx/flasker/blob/master/LICENSE.md).
