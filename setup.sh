#! /bin/bash
OLD_DIR=`pwd`
if [ $# -eq 0 ]
then
	echo "no initial args"
	ANNEX_DIR=/home/InformaCam/unveillance_remote
	ANACONDA_DIR=/home/InformaCam/anaconda
	UV_SERVER_HOST="192.168.1.105"
	UV_UUID="informacam-test"
else
	ANNEX_DIR=$1
	ANACONDA_DIR=$2
	UV_SERVER_HOST=$3
	UV_UUID=$4
fi

GPG_DIR=$OLD_DIR/.gnupg
FORMS_ROOT=$OLD_DIR/forms
USER_CONFIG=$OLD_DIR/lib/Annex/conf/annex.config.yaml

echo gpg_homedir: $GPG_DIR >> $USER_CONFIG
echo informacam.forms_root: $FORMS_ROOT >> $USER_CONFIG
mkdir $FORMS_ROOT

sudo apt-get install -y pkg-config libx264-dev make g++ python-setuptools yasm
cd lib/FFmpeg
./configure
make
sudo make install

sudo apt-get install -y ffmpeg2theora

JPEG_TOOLS_DIR=$OLD_DIR/lib/jpeg
cd $JPEG_TOOLS_DIR/jpeg-redaction/lib
make
g++ -L . -lredact jpeg.cpp jpeg_decoder.cpp jpeg_marker.cpp debug_flag.cpp byte_swapping.cpp iptc.cpp tiff_ifd.cpp tiff_tag.cpp j3mparser.cpp -o ../../j3mparser.out
make clean

# DO YOU HAVE JAVA-JDK and ANT?
cd $JPEG_TOOLS_DIR/JavaMediaHasher
ant compile dist
cp dist/JavaMediaHasher.jar $JPEG_TOOLS_DIR
ant clean

echo jpeg_tools_dir: $JPEG_TOOLS_DIR >> $USER_CONFIG

echo "***********************************"
echo "NOW ANNEX SETUP..."
echo $OLD_DIR/lib/Annex

cd $OLD_DIR/lib/Annex
chmod +x setup.sh
ls -la
./setup.sh $OLD_DIR $ANNEX_DIR $ANACONDA_DIR

echo export UV_SERVER_HOST="'"$UV_SERVER_HOST"'" >> .bashrc
echo export UV_UUID="'"$UV_UUID"'" >> .bashrc
source .bashrc

echo "**************************************************"
echo 'Initing git annex on '$ANNEX_DIR'...'
cd $ANNEX_DIR
git init
mkdir .git/hooks
cp $OLD_DIR/post-receive .git/hooks
chmod +x .git/hooks/post-receive

git annex init "unveillance_remote"
git annex untrust web
git checkout -b master

echo "**************************************************"
echo "Installing other python dependencies..."
cd $OLD_DIR

cd lib/python-gnupg
make install
cd ../

cd lib/Annex/lib/Worker/Tasks
ln -s $OLD_DIR/Tasks/* .
ls -la

cd ../Models
ln -s $OLD_DIR/Models/* .
ls -la

cd $OLD_DIR/lib/Annex
python unveillance_annex.py -firstuse
