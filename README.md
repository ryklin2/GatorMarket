A fullstack webapp made in React and Flask using a mySQL database allowing students and faculty to schedule, meet up, and exchange goods on campus.

Optimized and limited for usage on a free AWS server in the docker-compose. 

Test images have been removed from

## How to run

- install MySQL.
- install docker and all dependencies to run it in your OS

- docker compose build --up
or
- docker-compose build --up
depending on your OS

You may also initiate all 3 services searately to  run them outside of a virtual enviornment, but you will have to create the database using init.sql, the app using app.jsx and npm install + npm start, and the flask server using pip install requirements.txt and python run.

This was a group assignment completed with Yash, Dev, Hseuh, and Kyle.
