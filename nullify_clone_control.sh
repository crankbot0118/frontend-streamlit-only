#!/bin/sh
#################################################################################################
# nullify_clone_control.sh <dbname> <clone_run_id>
#
# VIGT Clone Automation — nullify clone control checkpoint.
#
# Called by agent.py before abort cleanup when the operator aborts a failed run.
# Empties $CLONE_CONTROL_FILE so master_clone.sh cannot resume if re-triggered.
#
# DB status is handled by the dashboard backend + master_clone.sh step rows;
# this script only touches the local checkpoint file.
#
# Usage: nullify_clone_control.sh <dbname> <clone_run_id>
#################################################################################################

if [ "$1" = "" ] || [ "$2" = "" ]
then
echo "Usage: nullify_clone_control.sh <dbname> <clone_run_id>"
exit 1
fi

_VALIDATE_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
. "${_VALIDATE_DIR}/vigt_validate_args.sh"
vigt_validate_shell_args "$1" "$2"

if [ -z "${INSTANCE_CLONE_DIR:-}" ]; then
echo "INSTANCE_CLONE_DIR is not set. Export it from the repo .env before running this script."
exit 1
fi

CLONE_RUN_ID=$2

. ${INSTANCE_CLONE_DIR}/${1}/env/DB/${1}_db.env

NULLIFY_LOG=${LOG_DIR}/nullify_clone_control_${CLONE_RUN_ID}_`date +"%Y%m%d_%H%M%S"`.log

echo "##############################################################################################" > $NULLIFY_LOG
echo "  nullify_clone_control.sh - Started : `date +"%Y:%m:%d %H:%M:%S"`" >> $NULLIFY_LOG
echo "  VIGT Clone Run ID : $CLONE_RUN_ID" >> $NULLIFY_LOG
echo "##############################################################################################" >> $NULLIFY_LOG

if [ -e $CLONE_CONTROL_FILE ]
then
    current_step=`cat $CLONE_CONTROL_FILE`
    echo "Control file exists. Current step was: $current_step" >> $NULLIFY_LOG
    cat /dev/null > $CLONE_CONTROL_FILE
    echo "Control file nullified: $CLONE_CONTROL_FILE" >> $NULLIFY_LOG
else
    echo "Control file does not exist — nothing to nullify: $CLONE_CONTROL_FILE" >> $NULLIFY_LOG
fi

echo "nullify_clone_control.sh completed - `date +"%Y:%m:%d %H:%M:%S"`" >> $NULLIFY_LOG

exit 0
