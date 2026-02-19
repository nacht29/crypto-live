# build image
DATE="${1:-$(date +%Y%m%d)}"
IMAGE_REPO="nacht29/crypto-live"
IMAGE_TAG="crypto-live-${DATE}"
IMAGE_NAME="crypto-live"
FULL_IMAGE="${IMAGE_REPO}:${IMAGE_TAG}"

sudo DOCKER_BUILDKIT=1 sudo docker build -t "${IMAGE_NAME}" .

# pushing image to Docker Hub
sudo docker tag "${IMAGE_NAME}" "${FULL_IMAGE}"
sudo docker push "${FULL_IMAGE}"

# option 1
sudo docker run --rm -it \
	-e AWS_PROFILE=crypto-live-pipeline01 \
	-e S3_WRITE=1 \
	-e DYNAMO_WRITE=0 \
	-v /home/nacht29/.aws/config:/root/.aws/config:ro \
	-v /home/nacht29/.aws/credentials:/root/.aws/credentials:ro \
	"${FULL_IMAGE}"

# # option 2
# sudo docker compose up
