1. Install Docker

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
```

2. Install BuildX plug-in:

```bash
sudo apt-get install docker-buildx-plugin
```

3. Enable BuildKit in /etc/docker/daemon.json

```bash
{
  "features": {
    "buildkit": true
  }
}
```

4. Restart Docker

```bash
sudo systemctl restart docker
```

5. Run `docker build`

```bash
DOCKER_BUILDKIT=1 sudo docker build -t "crypto-live" .
```
