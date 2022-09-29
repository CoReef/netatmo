FROM python:3
LABEL maintainer sturm@uni-trier.de
RUN apt-get update && apt-get install -y
WORKDIR picker
COPY requirements.txt ./
COPY *.py ./
RUN pip install --no-cache-dir -r requirements.txt
CMD [ "python", "netatmo_coreef.py", "--file", "/coreef/keys/netatmo.json", "--outdir", "/coreef/netatmo", "--poll", "600" ]

