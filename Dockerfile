FROM fsfe/reuse:latest

RUN mkdir /project

WORKDIR /project

COPY check-git.sh /bin/

ENTRYPOINT ["check-git.sh"]
