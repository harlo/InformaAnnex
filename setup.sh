#! /bin/bash
THIS_DIR=`pwd`

if [ $# -eq 0 ]
then
	echo "{}" > $THIS_DIR/lib/Annex/conf/informa.secrets.json
	WITH_CONFIG=$THIS_DIR/lib/Annex/conf/informa.secrets.json
else
	WITH_CONFIG=$1
fi

cd lib/Annex
./setup.sh $WITH_CONFIG
source ~/.bash_profile
sleep 2

cd $THIS_DIR

sudo apt-get install -y zip unzip pkg-config libx264-dev make g++ python-setuptools yasm ant openjdk-7-jdk lsof libgd2-xpm-dev libpuzzle-dev libjpeg62

FFMPEG_VERSION=`which ffmpeg`
if [[ $FFMPEG_VERSION == *bin/ffmpeg ]]
then
	echo "ffmpeg already installed.  Skipping"
else
	cd lib/FFmpeg
	./configure
	make
	sudo make install
	cd $THIS_DIR
fi

FFMPEG2_VERSION=`which ffmpeg2theora`
if [[ $FFMPEG2_VERSION == *bin/ffmpeg2theora ]]
then
	echo "ffmpeg2theora already installed.  Skipping"
else
	sudo apt-get install -y ffmpeg2theora
fi

LIBPUZZLE_VERSION=`which puzzle-diff`
if [[ $LIBPUZZLE_VERSION == *bin/puzzle-diff ]]
then
	echo "puzzle-diff already installed. Skipping"
else
	wget -O lib/libpuzzle-0.11.tar.gz http://download.pureftpd.org/pub/pure-ftpd/misc/libpuzzle/releases/libpuzzle-0.11.tar.gz
	tar -xvzf lib/libpuzzle-0.11.tar.gz -C lib/
	rm lib/libpuzzle-0.11.tar.gz

	cd $THIS_DIR/lib/libpuzzle-0.11
	./configure
	make
	sudo make install
	cd $THIS_DIR
fi

JPEG_TOOLS_DIR=$THIS_DIR/lib/jpeg
cd $JPEG_TOOLS_DIR/jpeg-redaction/lib
make
g++ -L . -lredact jpeg.cpp jpeg_decoder.cpp jpeg_marker.cpp debug_flag.cpp byte_swapping.cpp iptc.cpp tiff_ifd.cpp tiff_tag.cpp j3mparser.cpp -o ../../j3mparser.out
make clean

cd $JPEG_TOOLS_DIR/JavaMediaHasher
ant compile dist
cp dist/JavaMediaHasher.jar $JPEG_TOOLS_DIR
ant clean

cd $THIS_DIR/lib/python-gnupg
make install

cd $THIS_DIR/lib/Annex/lib/Worker/Tasks
ln -s $THIS_DIR/Tasks/* .
ls -la

cd $THIS_DIR/lib/Annex/lib/Worker/Models
ln -s $THIS_DIR/Models/* .
ls -la

cd $THIS_DIR
pip install --upgrade -r requirements.txt
python setup.py $1

cd lib/Annex
chmod 0400 conf/*
python unveillance_annex.py -firstuse
