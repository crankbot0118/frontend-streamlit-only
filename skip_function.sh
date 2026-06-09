#!/bin/sh
#################################################################################################
# skip_function.sh <dbname> <clone_run_id>
#
# VIGT Clone Automation — advance clone control checkpoint after operator SKIP.
#
# Called by agent.py after the dashboard backend inserts SKIPPED rows for the
# failed step. Advances $CLONE_CONTROL_FILE to the next step so master_clone.sh
# resumes from the following function on relaunch.
#
# Usage: skip_function.sh <dbname> <clone_run_id>
#################################################################################################

if [ "$1" = "" ] || [ "$2" = "" ]
then
echo "Usage: skip_function.sh <dbname> <clone_run_id>"
exit 1
fi

_VALIDATE_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
. "${_VALIDATE_DIR}/vigt_validate_args.sh"
vigt_validate_shell_args "$1" "$2"

CLONE_RUN_ID=$2

INSTANCE_CLONE_DIR=/u02/shared/AUTOMATION/Clone_Auto/Instances
. ${INSTANCE_CLONE_DIR}/${1}/env/DB/${1}_db.env

SKIP_LOG=${LOG_DIR}/skip_function_${CLONE_RUN_ID}_`date +"%Y%m%d_%H%M%S"`.log

echo "##############################################################################################" > $SKIP_LOG
echo "  skip_function.sh - Started : `date +"%Y:%m:%d %H:%M:%S"`" >> $SKIP_LOG
echo "  VIGT Clone Run ID : $CLONE_RUN_ID" >> $SKIP_LOG
echo "##############################################################################################" >> $SKIP_LOG

# Step order must match master_clone.sh and clone_functions seed data.
STEP_ORDER="
apps_shutdown
db_shutdown
db_mount_restrict
db_drop
db_nomount
db_restore
db_startup
db_validate_temp
db_rename_cdb
db_rename_pdb
db_util_file
db_conc_clean
db_autoconfig
db_custom_users
db_custom_directories
ebs_binaries_cleanup
ebs_binaries_download
ebs_binaries_untar
ebs_adcfg_primary_node
ebs_adcfg_secondary_node
ebs_fndcpass
ebs_start_run_admin_server
ebs_context_updates
ebs_soft_link_updates
ebs_autoconfig
ebs_profile_resp_conc_updates
ebs_custom_updates
ebs_stop_run_admin_server
ebs_integrations
ebs_custom_patch_fs_updates
ebs_final_apps_shutdown
db_final_shutdown
db_final_startup
db_final_autoconfig
ebs_final_autoconfig
ebs_final_apps_startall
"

if [ ! -e $CLONE_CONTROL_FILE ]
then
echo "ERROR: CLONE_CONTROL_FILE not found: $CLONE_CONTROL_FILE" >> $SKIP_LOG
exit 1
fi

if [ ! -s $CLONE_CONTROL_FILE ]
then
echo "ERROR: CLONE_CONTROL_FILE is empty: $CLONE_CONTROL_FILE" >> $SKIP_LOG
exit 1
fi

current_step=`cat $CLONE_CONTROL_FILE`
echo "Current step in control file: $current_step" >> $SKIP_LOG

found=0
next_step=""

for step in $STEP_ORDER
do
    if [ $found -eq 1 ]
    then
        next_step=$step
        break
    fi
    if [ "$step" = "$current_step" ]
    then
        found=1
    fi
done

if [ $found -eq 0 ]
then
echo "ERROR: Current step '$current_step' not found in step order" >> $SKIP_LOG
exit 1
fi

if [ "$next_step" = "" ]
then
echo "Current step is the last step ($current_step) — nullifying control file" >> $SKIP_LOG
cat /dev/null > $CLONE_CONTROL_FILE
else
echo "Advancing control file: $current_step -> $next_step" >> $SKIP_LOG
echo "$next_step" > $CLONE_CONTROL_FILE
echo "Control file updated to: $next_step" >> $SKIP_LOG
fi

echo "skip_function.sh completed - `date +"%Y:%m:%d %H:%M:%S"`" >> $SKIP_LOG

exit 0
