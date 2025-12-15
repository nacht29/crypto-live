# build image
sudo DOCKER_BUILDKIT=1 sudo docker build -t "crypto-live" .

# pushing image to Docker Hub
sudo docker tag crypto-live nacht29/crypto-live:latest
sudo docker push nacht29/crypto-live:latest

# run image
# can be done with 2 options

# option 1
sudo docker run --rm -it \
	-e AWS_PROFILE=crypto-live-pipeline01 \
	-v /home/nacht29/.aws/config:/root/.aws/config:ro \
	-v /home/nacht29/.aws/credentials:/root/.aws/credentials:ro \
	crypto-live

# option 2
sudo docker compose up
