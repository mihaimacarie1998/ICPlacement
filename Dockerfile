FROM inveniosoftware/centos8-python:3.7
MAINTAINER icplacement
USER root
RUN mkdir -p /mnt/IC_Placement
RUN cd /mnt/IC_Placement
COPY . /mnt/IC_Placement/
ENV LD_LIBRARY_PATH="/usr/local/lib64/:${LD_LIBRARY_PATH}"
RUN yum install mesa-libGL -y
RUN python --version
RUN echo $LD_LIBRARY_PATH
RUN strings /usr/lib64/libstdc++.so.6 | grep CXXABI
RUN pip install --upgrade pip
RUN python -m venv venv
RUN source venv/bin/activate
RUN pip install -r /mnt/IC_Placement/requirements.txt
EXPOSE 80 80
ENTRYPOINT ["/usr/bin/python", "/mnt/IC_Placement/app.py"]
CMD ["/usr/bin/echo", "success"]