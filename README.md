# SkyLeaf antispam server.

## How to start

docker build . -t node
docker container run -p 25:25 -d --name skyleaf node


## Configuration
It is controlled through a configuration file "/main/configuration_namager.configuration.json". The system automatically applies the configuration file every 2 minutes.
