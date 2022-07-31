FROM continuumio/miniconda3

RUN /opt/conda/bin/conda config --add channels conda-forge && /opt/conda/bin/conda update \
    -y conda && /opt/conda/bin/conda install \
    -y geopandas contextily matplotlib geoplot

WORKDIR /app

COPY . .

CMD ["python", "test.py"]