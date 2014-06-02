!# /bin/bash
THIS_DIR=`pwd`

# add forms to conf
# import key and delete

# create task manually
curl -X POST http://localhost:9200/unveillance/$TASK_ID -d {\
	"task_path" : "J3M.forms.initForms", \
	"queue" : $UV_UUID \
}

# run task
curl -X GET http://localhost:8889/task/$TASK_ID

# run inner script
cd lib/Annex
./init_local_remote.sh