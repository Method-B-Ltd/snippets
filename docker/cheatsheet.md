List all running Docker containers:
```bash
docker ps
```

List all Docker containers (running and stopped):
```bash
docker ps -a
```

Stop all running Docker containers:
```bash
docker stop $(docker ps -q)
```

Show the 10 largest Docker images:
```bash
docker images | head -n 1 && docker images | grep -v REPOSITORY | sort -k 7 -n -r | head -n 10
```

Delete all versions of a docker image:
```bash
docker rmi $(docker images -q <image_name>)
```

