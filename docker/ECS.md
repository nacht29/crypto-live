### Build image
```bash
export DOCKER_BUILDKIT=1
docker build -t crypto-live .
```

### Create ECR repo
```bash
aws --profile crypto-live-ECS ecr create-repository --repository-name crypto-live
```

On success, you will see this payload:

```json
{
	"repository": {
		"repositoryArn": "arn:aws:ecr:ap-southeast-1:068561046254:repository/crypto-live",
		"registryId": "068561046254",
		"repositoryName": "crypto-live",
		"repositoryUri": "068561046254.dkr.ecr.ap-southeast-1.amazonaws.com/crypto-live",
		"createdAt": "2025-11-23T04:00:23.953000+08:00",
		"imageTagMutability": "MUTABLE",
		"imageScanningConfiguration": {
			"scanOnPush": false
		},
		"encryptionConfiguration": {
			"encryptionType": "AES256"
		}
	}
}
```

### Get account ID
```bash
aws --profile crypto-live-ECS sts get-caller-identity --query Account --output text 068561046254
```

### AWS ECR log-in

```bash
aws --profile crypto-live-ECS ecr get-login-password --region ap-southeast-1 | docker login --username AWS --password-stdin 068561046254.dkr.ecr.ap-southeast-1.amazonaws.com
```

### Tag and push

``` bash
docker tag nacht29/crypto-live:crypto-live-20260218 068561046254.dkr.ecr.ap-southeast-1.amazonaws.com/crypto-live:crypto-live-20260218
docker push 068561046254.dkr.ecr.ap-southeast-1.amazonaws.com/crypto-live:crypto-live-20260218
```

### BuildX error

```bash
sudo apt-get update
sudo apt-get install docker-buildx-plugin docker-compose-plugin
```