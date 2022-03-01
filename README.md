# ODC Stacifier


NOTE! This is just a proof of concept.

A far better implementation is [Rio-STAC](https://github.com/developmentseed/rio-stac).




A super simple example of creating a STAC metadata file for some datasets (spatial rasters).

This tool also creates a minimum viable EO3 product and dataset definitions.

## Running locally

First, install the required tools: `pip3 install -r requirements.txt`.

Next, use Make to get the SRTM tile used for testing, `make examples/srtm_66_21.zip` and then unzip
with `make examples/srtm/srtm_66_21.tif` and now you can use the full command, using make like
`make test-srtm` or in full form like:

``` bash
python3 stac-simple.py \
  --extension=".tif" \
  --default-date="2020-06-30T12:00Z" \
  --platform=srtm \
  --band-name=elevation \
  --band-type=int16 \
  --band-nodata=-32768.0 \
  --create-product \
  --no-cog-convert \
  examples/srtm
```

Some basic examples are included in the examples directory, and dynamic examples can be generated
using the above commands.
