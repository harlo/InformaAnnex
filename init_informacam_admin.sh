#! /bin/bash
ASSET_DIR=`pwd`
ANNEX_ROOT=$1

# import key and delete
gpg --allow-secret-key-import --import informacam.gpg.priv_key.file
rm informacam.gpg.priv_key.file

# add forms to conf
for f in *
do
	if echo "$f" | grep '^informacam.form.*' > /dev/null ; then
		mv $f $ANNEX_ROOT/conf/
	fi
done

# create task manually
curl -X PUT http://localhost:8889/task/ -d '{ "task_path" : "J3M.forms.initForms" }'

# run inner script
cd $ANNEX_ROOT
./init_local_remote.sh $ASSET_DIR/unveillance.local_remote.pub_key