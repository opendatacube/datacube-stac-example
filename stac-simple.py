#!/usr/bin/env python

import datetime
import json
import pathlib

import click
import jinja2
import pystac
import rasterio
from odc.index.stac import stac_transform
from pyproj import Transformer
from rio_cogeo.cogeo import cog_translate, cog_validate
from rio_cogeo.profiles import cog_profiles

output_profile = cog_profiles.get("deflate")
output_profile.update(dict(nodata=0), crs="epsg:28355")

template = jinja2.Template(
    """
name: {{platform}}
description: Auto-generated product example for {{platform}}
metadata_type: eo3

metadata:
  product:
    name: {{platform}}

measurements:
- name: '{{band_name}}'
  units: '1'
  dtype: '{{band_type}}'
  nodata: {{band_nodata}}
...
"""
)


def get_datetime(raster):
    file_name = raster.stem
    date_string = file_name.split("_")[3]
    date = datetime.datetime.strptime(date_string, "%Y%m%d%H%M")
    return date.isoformat() + "Z"


def get_geometry(bbox, from_crs):
    transformer = Transformer.from_crs(from_crs, 4326)
    bbox_lonlat = [
        [bbox.left, bbox.bottom],
        [bbox.left, bbox.top],
        [bbox.right, bbox.top],
        [bbox.right, bbox.bottom],
        [bbox.left, bbox.bottom],
    ]
    geometry = {
        "type": "Polygon",
        "coordinates": [list(transformer.itransform(bbox_lonlat))],
    }
    return geometry, bbox_lonlat


def convert_to_cog(raster, validate=True):
    out_path = str(raster.with_suffix(".tif")).replace(" ", "_")
    assert raster != out_path, "Can't convert to files of the same name"
    cog_translate(raster, out_path, output_profile, quiet=True)
    if validate:
        cog_validate(out_path)
    return pathlib.Path(out_path)


def create_stac(raster, platform, band_name, default_date):
    transform = None
    shape = None
    crs = None

    with rasterio.open(raster) as dataset:
        transform = dataset.transform
        shape = dataset.shape
        crs = dataset.crs.to_epsg()
        bounds = dataset.bounds

    date_string = default_date
    if not date_string:
        date_string = get_datetime(raster)
    geometry, bbox = get_geometry(bounds, crs)
    stac_dict = {
        "id": raster.stem.replace(" ", "_"),
        "type": "Feature",
        "stac_version": "1.0.0-beta.2",
        "stac_extensions": [
            "proj"
        ],
        "properties": {"platform": platform, "datetime": date_string, "proj:epsg": crs},
        "bbox": bbox,
        "geometry": geometry,
        "assets": {
            band_name: {
                "title": f"Data file for {band_name}",
                "type": "image/tiff; application=geotiff; profile=cloud-optimized",
                "roles": ["data"],
                "href": raster.stem + raster.suffix,
                "proj:shape": shape,
                "proj:transform": transform,
            }
        },
    }
    with open(raster.with_suffix(".json"), "w") as f:
        json.dump(stac_dict, f, indent=2)

    with open(raster.with_suffix(".odc-dataset.json"), "w") as f:
        json.dump(stac_transform(stac_dict), f, indent=2)

    return None


def process_rasters(rasters, platform, band_name, cog_convert, default_date):
    for raster in rasters:
        try:
            if cog_convert:
                raster = convert_to_cog(raster)
            create_stac(raster, platform, band_name, default_date)
        except Exception as e:
            print(f"Failed to process {raster} with exception {e}")


@click.command("create-odc-stac")
@click.option(
    "--extension",
    default=".tif",
    type=str,
    help="Extension of files to work on.",
)
@click.option(
    "--default-date",
    default=None,
    type=str,
    help="A date for the file. Todo: work out how to make this magic.",
)
@click.option(
    "--platform",
    type=str,
    required=True,
    help="Platform name for the product",
)
@click.option(
    "--band-name",
    type=str,
    required=True,
    help="Band name for the asset/measurement",
)
@click.option(
    "--band-type",
    type=str,
    default="uint8",
    help="Band date type for the band",
)
@click.option(
    "--band-nodata",
    type=float,
    default=0,
    help="Band data type for the band",
)
@click.option(
    "--create-product/--no-create-product",
    is_flag=True,
    default=True,
    help=("Creates a basic EO3 product definition"),
)
@click.option(
    "--cog-convert/--no-cog-convert",
    is_flag=True,
    default=False,
    help=("Converts files to Cloud Optimised GeoTIFFs"),
)
@click.argument("directory", type=str, nargs=1)
def cli(
    extension,
    default_date,
    platform,
    create_product,
    band_name,
    band_type,
    band_nodata,
    cog_convert,
    directory,
):
    if create_product:
        with open(pathlib.Path(directory) / f"{platform}.odc-product.yaml", "wt") as f:
            f.write(
                template.render(
                    platform=platform,
                    band_name=band_name,
                    band_type=band_type,
                    band_nodata=band_nodata,
                )
            )
    rasters = pathlib.Path(directory).glob("**/*" + extension)
    process_rasters(rasters, platform, band_name, cog_convert, default_date)


if __name__ == "__main__":
    cli()
