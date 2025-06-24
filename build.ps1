docker stop harbormaster
docker rm harbormaster
docker build --no-cache -t djlactose/harbormaster ./
docker push djlactose/harbormaster
