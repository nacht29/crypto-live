### AWS CLI installation (WSL)

1. Download and extract installer

```bash
cd /tmp
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
```
2. Run installer

```bash
sudo ./aws/install
```

3. Confirm with

```bash
aws --version
```

### IAM credentials

1. Configure with profile flag

```bash
aws configure --profile crypto-live-pipeline01
```

2. Fill in access key details

```bash
AWS Access Key ID: AKIA...
AWS Secret Access Key: 
Default region name: ap-southeast-1
Default output format: json
```