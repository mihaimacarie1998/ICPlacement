1. copy to work vm installed docker
	copy BaseDockerfile, IC_Placement and MainDockerfile to /mnt in vm installed docker
	
2. Base image build
	$ cp /mnt/BaseDockerfile/Dockerfile /mnt/
	$ cd /mnt
	$ docker build ./ -t centos7-icplacement:latest
	$ rm -rf Dockerfile
	
3. Main image build
	$ cp /mnt/MainDockerfile/Dockerfile /mnt/
	$ cd /mnt
	$ docker build ./ -t icplacement:latest
	$ rm -rf Dockerfile
	
4. Run
	$ docker run -d -p 80:80 icplacement