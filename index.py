import json
import os
import rasterio as io
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine

json.load(open(file=os.path.join(os.getcwd(),"config.json")))["constring"]

# after adding a geometry column to geoindicators
constring = json.load(open(file=os.path.join(os.getcwd(),"config.json")))["constring"]
tifpath = json.load(open(file=os.path.join(os.getcwd(),"config.json")))["tifpath"]
sqlstatement = json.load(open(file=os.path.join(os.getcwd(),"config.json")))["sqlstatement"]

eng = create_engine(constring)
gi = gpd.read_postgis(sqlstatement, eng, geom_col="wkb_geometry")

def extract_modis_values(
                            geomdf: gpd.GeoDataFrame,
                            localtifpath: str
                        ):
    """
    extract values from local geotiff using rasterio
    and a dataframe with a geometry field in points format(can be geopandas or shapely).

    args:
      geomdf: geodataframe from geopandas / dataframe with shapely geom column.
      localtifpath: string pointing to geotiff in local directory.

    returns dataframe
    """
    eng = create_engine(constring)
    rstr = io.open(localtifpath)
    band = rstr.read(1)

    final_dataframe = geomdf.filter(["PrimaryKey"])
    final_dataframe['modis_val'] = geomdf.wkb_geometry.apply(lambda x: band[rstr.index(x.x,x.y)])

    return final_dataframe

pgdf = extract_modis_values(gi,tifpath) 
pg = pgdf.copy(deep=True)
# get modis classes // can be from local csv or database
classes = pd.read_sql('select * from public.modis_classes;', eng)
# rename fields to facilitate merge
pg.rename(columns={"modis_val":"Value"}, inplace=True)
final = pg.merge(classes, on="Value", how="inner").filter(["PrimaryKey", "Name"])

# using pandas, sends dataframe with modis values to postgres
final.to_sql('modis_values', eng, schema='public_dev')