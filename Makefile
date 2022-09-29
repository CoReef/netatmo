build:
	docker build -t netatmo_image .
run:
	docker run -d --restart=unless-stopped --net=host -v v_coreef:/coreef --name netatmo_coreef netatmo_image
clean:
	find . -name '__pycache__' | xargs rm -rf;
