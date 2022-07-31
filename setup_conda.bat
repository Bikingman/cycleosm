cd C:\Users\dpatterson\OneDrive - Cambridge Systematics\Documents\code\process_national_osm
conda config --append channels conda-forge
conda create --name osm_nat_data_proc python=3.6 pandas numpy geopandas openpyxl sqlalchemy psycopg2 geoalchemy2 --yes
conda install -c conda-forge python-wget
conda install h3-py
conda install h3pandas
pip install osmium
conda activate osm_nat_data_proc 


