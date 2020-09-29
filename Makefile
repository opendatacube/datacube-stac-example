# Get elevation example
examples/srtm_66_21.zip:
	wget http://srtm.csi.cgiar.org/wp-content/uploads/files/srtm_5x5/tiff/srtm_66_21.zip \
		-O examples/srtm_66_21.zip

examples/srtm/srtm_66_21.tif:
	make examples/srtm_66_21.zip
	unzip examples/srtm_66_21.zip -d examples/srtm

test-srtm:
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

test-linescan:
	python3 stac-simple.py \
		--extension=".bsq" \
		--platform=linescan \
		--band-name=thermal \
		--band-type=uint8 \
		--band-nodata=0 \
		--create-product \
		--cog-convert \
		examples/test_input
