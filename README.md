Python library for extracting and standardizing large OSM datasets.

Extracts and standardizes bike facility information from OSM and exports a shapefile of the results. The shapefiles include facilities for the right and left side of the road, and minimum and maximum facility types for each segment, which follows levels of protection for bicyclists. One-way roads are treated a little differently. On these road types, the facility that provides the maximum protection is used for both the min and maximum facility types. This assumes riders will use the facilities that provide the maximum level of protection on one-way roads. 

![Denver Bike Facs](https://user-images.githubusercontent.com/22425199/218263077-a6554521-5697-40fa-824e-1051c4b46009.png)

![image](https://user-images.githubusercontent.com/22425199/218263087-fe33097f-ae0b-4449-9c7d-3e9585d0d560.png)
