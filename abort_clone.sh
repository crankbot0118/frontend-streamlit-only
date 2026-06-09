#!/bin/sh
#################################################################################################
# abort_clone.sh <dbname> <clone_run_id>
#
# VIGT Clone Automation — local abort cleanup on the target instance.
#
# Called by agent.py after nullify_clone_control.sh when the operator aborts
# a failed run. Add any target-side cleanup commands here (stop processes,
# remove temp files, etc.). Run/step status in PostgreSQL is already set by
# the dashboard backend before this script runs.
#
# Usage: abort_clone.sh <dbname> <clone_run_id>
#################################################################################################

if [ "$1" = "" ] || [ "$2" = "" ]
then
echo "Usage: abort_clone.sh <dbname> <clone_run_id>"
exit 1
fi

CLONE_RUN_ID=$2

INSTANCE_CLONE_DIR=/u02/shared/AUTOMATION/Clone_Auto/Instances
. ${INSTANCE_CLONE_DIR}/${1}/env/DB/${1}_db.env

ABORT_LOG=${LOG_DIR}/abort_clone_${CLONE_RUN_ID}_`date +"%Y%m%d_%H%M%S"`.log

echo "##############################################################################################" > $ABORT_LOG
echo "  abort_clone.sh - Started : `date +"%Y:%m:%d %H:%M:%S"`" >> $ABORT_LOG
echo "  VIGT Clone Run ID : $CLONE_RUN_ID" >> $ABORT_LOG
echo "##############################################################################################" >> $ABORT_LOG

# Placeholder for target-side abort cleanup. Extend with real commands as needed.
echo "No additional local abort actions configured." >> $ABORT_LOG

echo "abort_clone.sh completed - `date +"%Y:%m:%d %H:%M:%S"`" >> $ABORT_LOG

exit 0
