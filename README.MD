## why

Initial attemps to spatially join a geotiff raster on postgres took too long with queries such as this one: 

```
with test as (
	select * from public_dev."dataHeader" 
)
update public_dev."geoIndicators" as target
set modis_val = src.ras 
from (
	select test."PrimaryKey", st_value(rastr.rast,1,test.wkb_geometry) as ras 
	from gis.modis_merge as rastr 
	join test
	on st_intersects(test.wkb_geometry, st_convexhull(rastr.rast))
) as src 
where target."PrimaryKey" = src."PrimaryKey" 
```

After a raster image was sent to be stored in PG, this query would use the postgis geometry field to spatially join each point and extract a raster value with the ST_value() function.

However because the size of the raster was too extensive even having only one band, I opted to use an out-db method that would store the cloud-optimized-geotiff (produced by this script: link to repo ) on aws and only load pointers to the information on postgres, making the retrival faster. 

```

update public_dev."geoIndicators"
set modis_val = st_value(rastr.rast,1,public_dev."geoIndicators".wkb_geometry)
from gis.modis_merge_outdb as rastr 
WHERE st_intersects(public_dev."geoIndicators".wkb_geometry, st_convexhull(rastr.rast));

```

This did not work, as a bug in the used version of postgres did not permit enabling '/vsicurl', a virtual file system used by postgres to query the cloud optimized geoTIFF on AWS. 

The error persisted despite enabling full GDAL functionality, further suggesting it was a postgres bug:
```
SET postgis.gdal_enabled_drivers = 'ENABLE_ALL';
```

response:
```
ERROR:  rt_util_gdal_open: Cannot open VSICURL file. VSICURL disabled
CONTEXT:  PL/pgSQL function st_value(raster,integer,geometry,boolean) line 18 at RETURN
```


I had to manually create this join using python, and in order to do that I started by adding geometry to the "geoIndicators" to reduce the amount of joins in subsequent statements: 

```
alter table public_dev."geoIndicators" 
add column wkb_geometry GEOMETRY;

update public_dev."geoIndicators" as target
set wkb_geometry = dh.wkb_geometry
from public_dev."dataHeader" as dh
where target."PrimaryKey" = dh."PrimaryKey" ;
```

Once I manually created the modis_value table with python, this join populated the modis_landscape field after which I dropped the geometry field:

```
alter table public_dev."geoIndicators" 
add column modis_landcover varchar(100);

update public_dev."geoIndicators" as target
set modis_landcover = mv."Name"
from public_dev.modis_values as mv
where target."PrimaryKey" = mv."PrimaryKey" ;

alter table public_dev."geoIndicators"
drop column wkb_geometry;
```