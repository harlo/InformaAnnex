#! /bin/bash
THIS_DIR=`pwd`

cd lib/Annex
./setup.sh $THIS_DIR/unveillance.secrets.json
source ~/.bashrc
sleep 2

cd $THIS_DIR

<<DONE
sudo apt-get install -y pkg-config libx264-dev make g++ python-setuptools yasm ant openjdk-7-jdk lsof
cd lib/FFmpeg
./configure
make
sudo make install

sudo apt-get install -y ffmpeg2theora

JPEG_TOOLS_DIR=$THIS_DIR/lib/jpeg
cd $JPEG_TOOLS_DIR/jpeg-redaction/lib
make
g++ -L . -lredact jpeg.cpp jpeg_decoder.cpp jpeg_marker.cpp debug_flag.cpp byte_swapping.cpp iptc.cpp tiff_ifd.cpp tiff_tag.cpp j3mparser.cpp -o ../../j3mparser.out
make clean

# DO YOU HAVE JAVA-JDK and ANT?
cd $JPEG_TOOLS_DIR/JavaMediaHasher
ant compile dist
cp dist/JavaMediaHasher.jar $JPEG_TOOLS_DIR
ant clean
DONE

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
python setup.py

cd lib/Annex
python unveillance_annex.py -firstuse