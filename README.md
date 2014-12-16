# InformaCam-UnveillanceAnnex

First, a disclaimer:

This is __not__ security software.  I take security very seriously.  I am absolutely not perfect; none of us are; myself especially.  I've learned to value peer review very highly, and this has not been put through that yet.  I would not advocate using this on anything sensitive yet, and you should take certain cautions in deployment.  This is a swiss-army knife tool I built to get a certain job done.  It's working quite well for me, and I only want it to get better.


## Setup

1.	After cloning this repo, `cd /path/to/InformaAnnex` and pull down the necessary submodules with
	
	`git submodule update --init --recursive`

1.	Run `./setup.sh` or pre-configure the Frontend with a .json config file (see **Configure** for more info) with `./setup.sh /path/to/config.json`.
1.	Follow the prompts.

## Configure

You may create a .json config file with any of the following directives to suit your needs.

#### Configuration Directives

###### Local Directives

*	**ssh_root (str)**
	The full path to your SSH config

*	**annex_dir (str)**
	The full path to your local submission folder (which should not exist beforehand!)

*	**uv_server_host (str)**
	The Annex server's hostname

*	**uv_uuid (str)**
	The shortcode for the server

###### InformaCam-specific Directives

*	**org_name (str)**
	Organization name

*	**org_details (str)**
	Organization details

*	**gpg_dir (str)**
	The full path to your GPG Keychain for InformaCam

*	**gpg_priv_key (str)**
	The full path to your InformaCam private key

*	**repo (dict)**
	An InformaCam Repository object (see **Repos** for more information.)

#### Repos

InformaCam Annex can automatically pull submissions from Google Drive or from Globaleaks.  To register a repository in your .json configuration file (pre-setup), format your repository accordingly:

###### Google Drive

	{
		"source" : "google_drive",
		"asset_id" : "email to use for drive account",
		"account_type" : "user" or "service",
		"p12" : "path to p12 for authentication (ONLY for service account_type!)",
		"client_secrets" : "path to client_secrets.json for authentication (ONLY for service account_type!)",
		"client_id" : "client_id (ONLY for user account_type; check API console!)",
		"client_secret" : "client_secret (ONLY for user account_type; check API console!)"
	}

###### Globaleaks

	{
		"source" : "globaleaks",
		"asset_id" "your instance's context gus",
		"host" : "globaleaks server host",
		"asset_root" : "path to globaleaks assets on server",
		"user" : "globaleaks server user",
		"public_url" : "globaleaks instance .onion address",
		"identity_file" : "identity file to use to address globaleaks server"
	}

#### Forms

Your forms should be in .xml format, and adhere to the JavaRosa specification.  You can have as many forms as you'd like.  Make sure they are all in an accessible folder somewhere on the host.  You will be prompted for their absolute path during setup and they will be pulled in for use.

## Messaging

The Annex will broadcast the status of all tasks to connected web Frontend clients via websocket.

#### Format

Messages from the annex channel will have the following format:

	{
		"_id" : "c895e95034a4a37eb73b3e691e176d0b",
		"status" : 302,
		"doc_id" : "b721079641a39621e08741c815467115",
		"task_path" : "Image.preprocess_image.preprocessImage",
		"task_type" : "UnveillanceTask"
	}

The annex channel will also send messages acknowledging the status of the connection.  Developers can do with that what they will.  The `_id` field is the task's ID in our database, the `doc_id` field represents the document in question (where available).

#### Status Codes

*	**201 (Created)** Task has been registered.
*	**302 (Found)** Task is valid, and can start.
*	**404 (Not Found)** Task is not valid; cannot start.
*	**200 (OK)** Task completed; finishing.
*	**412 (Precondition Failed)** Task failed; will finish in failed state.
*	**205 (Reset Content)** Task persists, and will run again after the designated period.
*	**410 (Gone)** Task deleted from task queue.
