nuDiplomacy
===========

weppy based web version of Diplomacy game.

Development
-----------

Lock requirements:

    poetry export -f requirements.txt -o requirements.txt --without-hashes
    poetry export -f requirements.txt -o requirements.dev.txt --without-hashes --dev

First step is to make configuration files, should be enough to copy all the *yml.example* files in *config* folder to *.yml* ones.

Then you should build the docker image using docker-compose:

    docker-compose build

And migrate the database:

    docker-compose run --rm web weppy -a nudiplomacy migrations up

and run the setup:

    docker-compose run --rm web weppy -a nudiplomacy setup

### Game data

Some testing data is available for development, so you might run:

    docker-compose run --rm web weppy -a nudiplomacy add_map classic

to add the classic map and you might need a couple of test users for playing:

    docker-compose run --rm web weppy -a nudiplomacy create_test_data

Then you can login to the platform using *tester1@nudiplomacy.com* and *tester2@nudiplomacy.com*, both passwords are set to `foobar`.

Follow the game form to create a new game.
