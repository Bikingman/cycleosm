cd /Users/danielpatterson/Documents/GitHub/dockerfiles/conda-geopandas
docker build -t roads .
docker run -v $(pwd):/src -i -t -p 8888:8888 roads
conda activate roads



