docker build -t roads .
docker run -v $(pwd):/src -i -t -p 8888:8888 roads
conda activate roads
cd ..
cd src/


