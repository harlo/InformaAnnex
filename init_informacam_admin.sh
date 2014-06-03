#! /bin/bash
ASSET_DIR=`pwd`
ANNEX_ROOT=$1
USER_CONFIG=$ANNEX_ROOT/conf/local.config.yaml

if [ $# -eq 2 ]
then
	GNUPG_HOME=$2
else
	GNUPG_HOME=~/.gnupg
fi

# import key and delete
mkdir $GNUPG_HOME
echo informacam.gpg.homedir: $GNUPG_HOME >> $USER_CONFIG
echo informacam.gpg.priv_key.password: $(`cat informacam.gpg.priv_key.password`) >> $USER_CONFIG

gpg --allow-secret-key-import --import informacam.gpg.priv_key.file
rm informacam.gpg.priv_key.file
rm informacam.gpg.priv_key.password

# add forms to conf
for f in *
do
	if echo "$f" | grep '^informacam.form.*' > /dev/null ; then
		mv $f $ANNEX_ROOT/conf/
	fi
done

# create task manually
curl -X POST http://localhost:8889/task/ -d '{ "task_path" : "J3M.forms.initForms" }'

# run inner script
cd $ANNEX_ROOT
./init_local_remote.sh $ASSET_DIR/unveillance.local_remote.pub_key