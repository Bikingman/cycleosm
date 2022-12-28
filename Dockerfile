

FROM continuumio/miniconda3

RUN apt-get update && apt-get install -y libopencv-dev  
RUN apt-get install build-essential cmake libboost-dev libexpat1-dev zlib1g-dev libbz2-dev

WORKDIR /app

# Create the environment:
COPY environment.yml .
RUN conda env create -f environment.yml 

# Make RUN commands use the new environment:
SHELL ["conda", "run", "-n", "roads", "/bin/bash", "-c"]

ENV PYTHONPATH "${PYTHONPATH}:/src/python"

# Demonstrate the environment is activated:
RUN echo "Make sure geopandas is installed:"
RUN python -c "import geopandas"