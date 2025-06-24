docker stop harbormaster
docker rm harbormaster
docker build --no-cache -t djlactose/harbormaster ./
docker run -d -v harbormaster_data:/data -v /var/run/docker.sock:/var/run/docker.sock -p 8080:8080 --name harbormaster djlactose/harbormaster