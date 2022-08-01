FROM bikingman/process_osm_national_dataset

RUN /opt/conda/bin/conda config --add channels conda-forge && /opt/conda/bin/conda update \
    -y conda && /opt/conda/bin/conda install \
    -y geopandas 

WORKDIR /app

COPY . .

CMD ["python", "test.py"]