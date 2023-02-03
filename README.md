Python library for extracting and standardizing large OSM datasets.

Extracts and standardizes bike facility information from OSM and exports a shapefile of the results. The shapefiles include facilities for the right and left side of the road, and minimum and maximum facility types for each segment, which follows levels of protection for bicyclists. One-way roads are treated a little differently. On these road types, the facility that provides the maximum protection is used for both the min and maximum facility types. This assumes riders will use the facilities that provide the maximum level of protection on one-way roads. 

![denver_bike_facs](https://user-images.githubusercontent.com/22425199/216670231-b31cc835-ecd0-4a19-9f0b-c0f22a4ea490.png)
