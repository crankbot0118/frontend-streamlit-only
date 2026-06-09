#!/bin/sh
#################################################################################################
# master_clone.sh <dbname> <clone_run_id>
#
# VIGT Clone Automation — target-instance clone driver.
#
# Args:
#   $1 = dbname        — instance key under INSTANCE_CLONE_DIR (e.g. uat)
#   $2 = clone_run_id  — passed by agent.py (e.g. 1000)
#
# PostgreSQL connection (from agent.py subprocess env or DB_* fallbacks):
#   PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD
#
# Step status updates go to clone_function_run_status only. Parent run status
# is rolled up by trg_sync_run_status; target lock by trg_sync_env_lock.
#
# function_id mapping (clone_functions table):
#   apps_shutdown=0 … ebs_final_apps_startall=350
#################################################################################################

if [ "$1" = "" ]
then
echo;echo
echo "Argument Not Provided, Please Pass the DB name as Argument"
echo "Usage: <scriptname> <dbname> <clone_run_id>"
echo "Aborting Clone Process"
echo;echo
exit 1
fi

if [ "$2" = "" ]
then
echo;echo
echo "clone_run_id Not Provided"
echo "Usage: <scriptname> <dbname> <clone_run_id>"
echo "Aborting Clone Process"
echo;echo
exit 1
fi

set -x
CLONE_RUN_ID=$2

INSTANCE_CLONE_DIR=/u02/shared/AUTOMATION/Clone_Auto/Instances
. ${INSTANCE_CLONE_DIR}/${1}/env/DB/${1}_db.env
caps_pdb_name=`echo ${TARGET_PDB_NAME}|tr 'a-z' 'A-Z'`

clone_start=`date +"%Y:%m:%d %H:%M:%S"`
echo "##############################################################################################" > $CLONE_LOG
echo "                                     Clone Start - $clone_start" >> $CLONE_LOG
echo "                                     VIGT Clone Run ID: $CLONE_RUN_ID" >> $CLONE_LOG
echo "##############################################################################################" >> $CLONE_LOG
echo >> $CLONE_LOG
echo "Log File = $CLONE_LOG"

# =============================================================================
# VIGT DB HELPER FUNCTIONS
# Step rows drive dashboard state; triggers sync parent run + env lock.
# =============================================================================

vigt_load_db_env()
{
if [ -z "$PGHOST" ]
then
    PGHOST=${DB_HOST:-}
    PGPORT=${DB_PORT:-5432}
    PGDATABASE=${DB_NAME:-}
    PGUSER=${DB_USER:-}
    PGPASSWORD=${DB_PASSWORD:-}
    export PGHOST PGPORT PGDATABASE PGUSER PGPASSWORD
fi
}

vigt_db()
{
vigt_load_db_env
psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -At -c "$1" 2>> "$CLONE_LOG"
}

step_name_to_fid()
{
    case "$1" in
        "apps_shutdown")               echo 0;;
        "db_shutdown")                 echo 10;;
        "db_mount_restrict")           echo 20;;
        "db_drop")                     echo 30;;
        "db_nomount")                  echo 40;;
        "db_restore")                  echo 50;;
        "db_startup")                  echo 60;;
        "db_validate_temp")            echo 70;;
        "db_rename_cdb")               echo 80;;
        "db_rename_pdb")               echo 90;;
        "db_util_file")                echo 100;;
        "db_conc_clean")               echo 110;;
        "db_autoconfig")               echo 120;;
        "db_custom_users")             echo 130;;
        "db_custom_directories")       echo 140;;
        "ebs_binaries_cleanup")        echo 150;;
        "ebs_binaries_download")       echo 160;;
        "ebs_binaries_untar")          echo 170;;
        "ebs_adcfg_primary_node")      echo 180;;
        "ebs_adcfg_secondary_node")    echo 190;;
        "ebs_fndcpass")                echo 200;;
        "ebs_start_run_admin_server")  echo 210;;
        "ebs_context_updates")         echo 220;;
        "ebs_soft_link_updates")       echo 230;;
        "ebs_autoconfig")              echo 240;;
        "ebs_profile_resp_conc_updates") echo 250;;
        "ebs_custom_updates")          echo 260;;
        "ebs_stop_run_admin_server")   echo 270;;
        "ebs_integrations")            echo 280;;
        "ebs_custom_patch_fs_updates") echo 290;;
        "ebs_final_apps_shutdown")     echo 300;;
        "db_final_shutdown")           echo 310;;
        "db_final_startup")            echo 320;;
        "db_final_autoconfig")         echo 330;;
        "ebs_final_autoconfig")        echo 340;;
        "ebs_final_apps_startall")     echo 350;;
        *)                             echo -1;;
    esac
}

vigt_set_log_location()
{
local log_path
log_path=`echo "$CLONE_LOG" | sed "s/'/''/g"`
vigt_db "
    UPDATE clone_run_status
    SET    log_location = '${log_path}',
           last_update  = NOW()
    WHERE  clone_run_id = ${CLONE_RUN_ID};
"
echo "VIGT: log_location set on clone_run_id=${CLONE_RUN_ID}" >> "$CLONE_LOG"
}

vigt_get_step_id()
{
local fid=$1
vigt_db "
    SELECT clone_function_run_id
    FROM   clone_function_run_status
    WHERE  clone_run_id = ${CLONE_RUN_ID}
      AND  function_id  = ${fid}
      AND  status       = 'PENDING'
    ORDER  BY clone_function_run_id DESC
    LIMIT  1;
"
}

vigt_step_start()
{
local step_id=$1
vigt_db "
    UPDATE clone_function_run_status
    SET    status     = 'RUNNING',
           start_time = NOW()
    WHERE  clone_function_run_id = ${step_id};
"
echo "VIGT: step_id=${step_id} marked RUNNING" >> "$CLONE_LOG"
}

vigt_step_done()
{
local step_id=$1
vigt_db "
    UPDATE clone_function_run_status
    SET    status   = 'COMPLETED',
           end_time = NOW()
    WHERE  clone_function_run_id = ${step_id};
"
echo "VIGT: step_id=${step_id} marked COMPLETED" >> "$CLONE_LOG"
}

vigt_step_fail()
{
local step_id=$1
vigt_db "
    UPDATE clone_function_run_status
    SET    status   = 'FAILED',
           end_time = NOW()
    WHERE  clone_function_run_id = ${step_id};
"
echo "VIGT: step_id=${step_id} marked FAILED" >> "$CLONE_LOG"
}

vigt_fail_run()
{
local step_id
step_id=`vigt_db "
    SELECT clone_function_run_id
    FROM   clone_function_run_status
    WHERE  clone_run_id = ${CLONE_RUN_ID}
      AND  status       = 'RUNNING'
    ORDER  BY clone_function_run_id DESC
    LIMIT  1;
"`
if [ -n "$step_id" ]
then
    vigt_step_fail "$step_id"
else
    echo "VIGT: no RUNNING step found to mark FAILED for clone_run_id=${CLONE_RUN_ID}" >> "$CLONE_LOG"
fi
}

vigt_set_log_location

# =============================================================================
# ORIGINAL send_running_clone_status_updates — REPLACED WITH VIGT DB CALL
# Original: sent email with clone log attachment.
# Now: updates DB step status so dashboard reflects real-time progress.
#
# Original signature: send_running_clone_status_updates <flag> <prev_step> <curr_step>
# We keep the same signature so all 36 call sites work unchanged.
# $1 = flag (0=normal, 1=with extra info) — kept for compatibility, unused now
# $2 = completed step name
# $3 = starting step name (or "clone_complete")
# =============================================================================
send_running_clone_status_updates()
{
local prev_step=$2
local curr_step=$3

echo "VIGT: send_running_clone_status_updates: $prev_step completed, $curr_step starting" >> "$CLONE_LOG"

if [ "$prev_step" != "script_start" ] && [ "$prev_step" != "clone_complete" ]
then
    local prev_fid=`step_name_to_fid "$prev_step"`
    if [ "$prev_fid" != "-1" ]
    then
        local prev_step_id=`vigt_db "
            SELECT clone_function_run_id
            FROM   clone_function_run_status
            WHERE  clone_run_id = ${CLONE_RUN_ID}
              AND  function_id  = ${prev_fid}
              AND  status       = 'RUNNING'
            ORDER  BY clone_function_run_id DESC
            LIMIT  1;
        "`
        if [ -n "$prev_step_id" ]
        then
            vigt_step_done "$prev_step_id"
        fi
    fi
fi

if [ "$curr_step" != "clone_complete" ]
then
    local curr_fid=`step_name_to_fid "$curr_step"`
    if [ "$curr_fid" != "-1" ]
    then
        local curr_step_id=`vigt_get_step_id "$curr_fid"`
        if [ -n "$curr_step_id" ]
        then
            vigt_step_start "$curr_step_id"
        fi
    fi
fi
}

# =============================================================================
# ORIGINAL check_run FUNCTION — UNCHANGED
# Reads $CLONE_CONTROL_FILE to determine if a step should run (proceed=0),
# be skipped as already done (proceed=99), or be blocked (proceed=1).
# =============================================================================
check_run()
{
echo "." >> $CLONE_LOG
echo "Inside check_run, parameter=$1" >> $CLONE_LOG
proceed=99
current_step=0
if [ -e $CLONE_CONTROL_FILE ]
then
    if [ -s $CLONE_CONTROL_FILE ]
    then
    current_process=`cat $CLONE_CONTROL_FILE`
    case "$current_process" in
    "apps_shutdown")        current_step=1;;
    "db_shutdown")          current_step=2;;
    "db_mount_restrict")    current_step=3;;
    "db_drop")              current_step=4;;
    "db_nomount")           current_step=5;;
    "db_restore")           current_step=6;;
    "db_startup")           current_step=7;;
    "db_validate_temp")     current_step=8;;
    "db_rename_cdb")        current_step=9;;
    "db_rename_pdb")        current_step=10;;
    "db_util_file")         current_step=11;;
    "db_conc_clean")        current_step=12;;
    "db_autoconfig")        current_step=13;;
    "db_custom_users")      current_step=14;;
    "db_custom_directories") current_step=15;;
    "ebs_binaries_cleanup") current_step=16;;
    "ebs_binaries_download") current_step=17;;
    "ebs_binaries_untar")   current_step=18;;
    "ebs_adcfg_primary_node") current_step=19;;
    "ebs_adcfg_secondary_node") current_step=20;;
    "ebs_fndcpass")         current_step=21;;
    "ebs_start_run_admin_server") current_step=22;;
    "ebs_context_updates")  current_step=23;;
    "ebs_soft_link_updates") current_step=24;;
    "ebs_autoconfig")       current_step=25;;
    "ebs_profile_resp_conc_updates") current_step=26;;
    "ebs_custom_updates")   current_step=27;;
    "ebs_stop_run_admin_server") current_step=28;;
    "ebs_integrations")     current_step=29;;
    "ebs_custom_patch_fs_updates") current_step=30;;
    "ebs_final_apps_shutdown") current_step=31;;
    "db_final_shutdown")    current_step=32;;
    "db_final_startup")     current_step=33;;
    "db_final_autoconfig")  current_step=34;;
    "ebs_final_autoconfig") current_step=35;;
    "ebs_final_apps_startall") current_step=36;;
    "syntax_check")         current_step=90;;
    *)                      current_step=99;;
    esac
    case "$1" in
    "apps_shutdown")        validate_step=1;;
    "db_shutdown")          validate_step=2;;
    "db_mount_restrict")    validate_step=3;;
    "db_drop")              validate_step=4;;
    "db_nomount")           validate_step=5;;
    "db_restore")           validate_step=6;;
    "db_startup")           validate_step=7;;
    "db_validate_temp")     validate_step=8;;
    "db_rename_cdb")        validate_step=9;;
    "db_rename_pdb")        validate_step=10;;
    "db_util_file")         validate_step=11;;
    "db_conc_clean")        validate_step=12;;
    "db_autoconfig")        validate_step=13;;
    "db_custom_users")      validate_step=14;;
    "db_custom_directories") validate_step=15;;
    "ebs_binaries_cleanup") validate_step=16;;
    "ebs_binaries_download") validate_step=17;;
    "ebs_binaries_untar")   validate_step=18;;
    "ebs_adcfg_primary_node") validate_step=19;;
    "ebs_adcfg_secondary_node") validate_step=20;;
    "ebs_fndcpass")         validate_step=21;;
    "ebs_start_run_admin_server") validate_step=22;;
    "ebs_context_updates")  validate_step=23;;
    "ebs_soft_link_updates") validate_step=24;;
    "ebs_autoconfig")       validate_step=25;;
    "ebs_profile_resp_conc_updates") validate_step=26;;
    "ebs_custom_updates")   validate_step=27;;
    "ebs_stop_run_admin_server") validate_step=28;;
    "ebs_integrations")     validate_step=29;;
    "ebs_custom_patch_fs_updates") validate_step=30;;
    "ebs_final_apps_shutdown") validate_step=31;;
    "db_final_shutdown")    validate_step=32;;
    "db_final_startup")     validate_step=33;;
    "db_final_autoconfig")  validate_step=34;;
    "ebs_final_autoconfig") validate_step=35;;
    "ebs_final_apps_startall") validate_step=36;;
    "syntax_check")         validate_step=90;;
    *)                      validate_step=99;;
    esac

    if [ "$current_step" -ne "99" ]
    then
    if [ "$current_step" = "$validate_step" ]
    then
    echo "Clone Control Process = $current_process, Requested Start = $1, proceeding" >> $CLONE_LOG
    if [ $current_step -eq 90 ]
    then
    proceed=90
    else
    proceed=0
    fi
    else
    if [ $validate_step -lt $current_step ]
    then
    echo "Validation step $1 already completed, skipping" >> $CLONE_LOG
    proceed=99
    if [ $current_step -eq 90 ]
    then
    proceed=90
    fi
    elif [ $validate_step -gt $current_step ] && [ $validate_step -ne 99 ]
    then
    if [ $validate_step -eq 90 ]
    then
    proceed=0
    else
    echo "Clone Control Process = $current_process, Requested Start = $1, Not proceeding as previous steps not completed" >> $CLONE_LOG
    proceed=1
    fi
    else
    echo "Clone Control Process = $current_process, Requested Start = $1, Unknown Requested Start" >> $CLONE_LOG
    proceed=1
    fi
    fi
    else
    echo "Unknown Clone Control value = $current_process, Aborting" >> $CLONE_LOG
    proceed=1
    fi
    else
    echo "Clone control File blank" >> $CLONE_LOG
    if [ "$1" = "apps_shutdown" ] || [ "$1" = "syntax_check" ]
    then
    echo "Clone control File Blank, starting with apps_shutdown" >> $CLONE_LOG
    echo "apps_shutdown" > $CLONE_CONTROL_FILE
    echo "Requested Start = $1, Starting with process $1" >> $CLONE_LOG
    proceed=0
    else
    echo "Clone control File blank, must start from apps_shutdown" >> $CLONE_LOG
    proceed=1
    fi
    fi
else
echo "Clone control File does not exist, created empty file" >> $CLONE_LOG
cat /dev/null > $CLONE_CONTROL_FILE
    if [ "$1" = "apps_shutdown" ]
    then
    echo "Starting with Apps Shutdown" >> $CLONE_LOG
    proceed=0
    else
    echo "Clone Status File blank, must start from apps_shutdown" >> $CLONE_LOG
    proceed=1
    fi
fi
if [ "$current_step" -ne 99 ]
then
echo "Exiting check_run, parameter=$1, proceed=$proceed" >> $CLONE_LOG
fi
}

# =============================================================================
# DUMMY STEP FUNCTION DEFINITIONS
# Each function simulates work with a sleep, then sets function_exit=0 (success).
# In the real script, replace the dummy body with the actual commands.
# The VIGT DB calls (vigt_step_start/done/fail) are called from
# send_running_clone_status_updates — NOT from inside the step functions directly.
# This preserves the original script architecture exactly.
# =============================================================================

apps_shutdown()
{
echo ".." >> $CLONE_LOG
apps_shutdown_start=`date +"%Y:%m:%d %H:%M:%S"`
echo "Inside apps_shutdown - $apps_shutdown_start" >> $CLONE_LOG
# DUMMY: replace with real apps shutdown commands
sleep 1
function_exit=0
apps_shutdown_end=`date +"%Y:%m:%d %H:%M:%S"`
echo "Exiting apps_shutdown - $apps_shutdown_end" >> $CLONE_LOG
unset apps_shutdown_start apps_shutdown_end
}

db_shutdown()
{
echo ".." >> $CLONE_LOG
db_shutdown_start=`date +"%Y:%m:%d %H:%M:%S"`
echo "Inside db_shutdown - $db_shutdown_start" >> $CLONE_LOG
# DUMMY: replace with real db shutdown commands
sleep 1
function_exit=0
db_shutdown_end=`date +"%Y:%m:%d %H:%M:%S"`
echo "Exiting db_shutdown - $db_shutdown_end" >> $CLONE_LOG
unset db_shutdown_start db_shutdown_end
}

db_mount_restrict()
{
echo ".." >> $CLONE_LOG
echo "Inside db_mount_restrict" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting db_mount_restrict" >> $CLONE_LOG
}

db_drop()
{
echo ".." >> $CLONE_LOG
echo "Inside db_drop" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting db_drop" >> $CLONE_LOG
}

db_nomount()
{
echo ".." >> $CLONE_LOG
echo "Inside db_nomount" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting db_nomount" >> $CLONE_LOG
}

db_restore()
{
echo ".." >> $CLONE_LOG
echo "Inside db_restore" >> $CLONE_LOG
sleep 2
function_exit=0
echo "Exiting db_restore" >> $CLONE_LOG
}

db_startup()
{
echo ".." >> $CLONE_LOG
echo "Inside db_startup" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting db_startup" >> $CLONE_LOG
}

db_validate_temp()
{
echo ".." >> $CLONE_LOG
echo "Inside db_validate_temp" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting db_validate_temp" >> $CLONE_LOG
}

db_rename_cdb()
{
echo ".." >> $CLONE_LOG
echo "Inside db_rename_cdb" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting db_rename_cdb" >> $CLONE_LOG
}

db_rename_pdb()
{
echo ".." >> $CLONE_LOG
echo "Inside db_rename_pdb" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting db_rename_pdb" >> $CLONE_LOG
}

db_util_file()
{
echo ".." >> $CLONE_LOG
echo "Inside db_util_file" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting db_util_file" >> $CLONE_LOG
}

db_conc_clean()
{
echo ".." >> $CLONE_LOG
echo "Inside db_conc_clean" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting db_conc_clean" >> $CLONE_LOG
}

db_autoconfig()
{
echo ".." >> $CLONE_LOG
echo "Inside db_autoconfig" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting db_autoconfig" >> $CLONE_LOG
}

db_custom_users()
{
echo ".." >> $CLONE_LOG
echo "Inside db_custom_users" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting db_custom_users" >> $CLONE_LOG
}

db_custom_directories()
{
echo ".." >> $CLONE_LOG
echo "Inside db_custom_directories" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting db_custom_directories" >> $CLONE_LOG
}

ebs_binaries_cleanup()
{
echo ".." >> $CLONE_LOG
echo "Inside ebs_binaries_cleanup" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting ebs_binaries_cleanup" >> $CLONE_LOG
}

ebs_binaries_download()
{
echo ".." >> $CLONE_LOG
echo "Inside ebs_binaries_download" >> $CLONE_LOG
sleep 2
function_exit=0
echo "Exiting ebs_binaries_download" >> $CLONE_LOG
}

ebs_binaries_untar()
{
echo ".." >> $CLONE_LOG
echo "Inside ebs_binaries_untar" >> $CLONE_LOG
sleep 2
function_exit=0
echo "Exiting ebs_binaries_untar" >> $CLONE_LOG
}

ebs_adcfg_primary_node()
{
echo ".." >> $CLONE_LOG
echo "Inside ebs_adcfg_primary_node" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting ebs_adcfg_primary_node" >> $CLONE_LOG
}

ebs_adcfg_secondary_node()
{
echo ".." >> $CLONE_LOG
echo "Inside ebs_adcfg_secondary_node" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting ebs_adcfg_secondary_node" >> $CLONE_LOG
}

ebs_fndcpass()
{
echo ".." >> $CLONE_LOG
echo "Inside ebs_fndcpass" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting ebs_fndcpass" >> $CLONE_LOG
}

ebs_start_run_admin_server()
{
echo ".." >> $CLONE_LOG
echo "Inside ebs_start_run_admin_server" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting ebs_start_run_admin_server" >> $CLONE_LOG
}

ebs_context_updates()
{
echo ".." >> $CLONE_LOG
echo "Inside ebs_context_updates" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting ebs_context_updates" >> $CLONE_LOG
}

ebs_soft_link_updates()
{
echo ".." >> $CLONE_LOG
echo "Inside ebs_soft_link_updates" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting ebs_soft_link_updates" >> $CLONE_LOG
}

ebs_autoconfig()
{
echo ".." >> $CLONE_LOG
echo "Inside ebs_autoconfig" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting ebs_autoconfig" >> $CLONE_LOG
}

ebs_profile_resp_conc_updates()
{
echo ".." >> $CLONE_LOG
echo "Inside ebs_profile_resp_conc_updates" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting ebs_profile_resp_conc_updates" >> $CLONE_LOG
}

ebs_custom_updates()
{
echo ".." >> $CLONE_LOG
echo "Inside ebs_custom_updates" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting ebs_custom_updates" >> $CLONE_LOG
}

ebs_stop_run_admin_server()
{
echo ".." >> $CLONE_LOG
echo "Inside ebs_stop_run_admin_server" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting ebs_stop_run_admin_server" >> $CLONE_LOG
}

ebs_integrations()
{
echo ".." >> $CLONE_LOG
echo "Inside ebs_integrations" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting ebs_integrations" >> $CLONE_LOG
}

ebs_custom_patch_fs_updates()
{
echo ".." >> $CLONE_LOG
echo "Inside ebs_custom_patch_fs_updates" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting ebs_custom_patch_fs_updates" >> $CLONE_LOG
}

ebs_final_apps_shutdown()
{
echo ".." >> $CLONE_LOG
echo "Inside ebs_final_apps_shutdown" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting ebs_final_apps_shutdown" >> $CLONE_LOG
}

db_final_shutdown()
{
echo ".." >> $CLONE_LOG
echo "Inside db_final_shutdown" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting db_final_shutdown" >> $CLONE_LOG
}

db_final_startup()
{
echo ".." >> $CLONE_LOG
echo "Inside db_final_startup" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting db_final_startup" >> $CLONE_LOG
}

db_final_autoconfig()
{
echo ".." >> $CLONE_LOG
echo "Inside db_final_autoconfig" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting db_final_autoconfig" >> $CLONE_LOG
}

ebs_final_autoconfig()
{
echo ".." >> $CLONE_LOG
echo "Inside ebs_final_autoconfig" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting ebs_final_autoconfig" >> $CLONE_LOG
}

ebs_final_apps_startall()
{
echo ".." >> $CLONE_LOG
echo "Inside ebs_final_apps_startall" >> $CLONE_LOG
sleep 1
function_exit=0
echo "Exiting ebs_final_apps_startall" >> $CLONE_LOG
}

clone_completion()
{
echo "##############################################################################################" >> $CLONE_LOG
echo "                              Clone Completed Successfully" >> $CLONE_LOG
echo "                              VIGT Clone Run ID: $CLONE_RUN_ID" >> $CLONE_LOG
echo "##############################################################################################" >> $CLONE_LOG
}

# =============================================================================
# SCRIPT EXECUTION — identical flow to original master_clone.sh
# Each step block:
#   1. check_run <step> — reads control file, sets proceed
#   2. if proceed=0: run the step, write next step to control file
#   3. if proceed=99: skip (already done)
#   4. send_running_clone_status_updates — now updates VIGT DB
# =============================================================================

proceed=1
exec_stat=0

check_run apps_shutdown

if [ $proceed = 0 ] && [ $current_step -ne 99 ]
then
apps_shutdown_start=`date +"%Y:%m:%d %H:%M:%S"`
echo "Running apps_shutdown - Started : $apps_shutdown_start" >> $CLONE_LOG
send_running_clone_status_updates 0 script_start apps_shutdown
apps_shutdown
proceed=$function_exit
if [ $proceed = 0 ]
then
echo "db_shutdown" > $CLONE_CONTROL_FILE
else
exec_stat=1
fi
elif [ $proceed = 99 ]
then
echo "Skipping apps_shutdown as step already completed" >> $CLONE_LOG
proceed=0
fi

if [ $proceed = 0 ]
then
apps_shutdown_end=`date +"%Y:%m:%d %H:%M:%S"`
echo "Completed apps_shutdown - Finished: $apps_shutdown_end" >> $CLONE_LOG
unset apps_shutdown_start apps_shutdown_end
check_run db_shutdown
else
if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]
then
exec_stat=1
echo "Failed apps_shutdown" >> $CLONE_LOG
fi
fi

if [ $proceed = 0 ]
then
db_shutdown_start=`date +"%Y:%m:%d %H:%M:%S"`
echo "Running db_shutdown - Started : $db_shutdown_start" >> $CLONE_LOG
function_exit=1
send_running_clone_status_updates 0 apps_shutdown db_shutdown
db_shutdown normal $DB_STOP_LOG
proceed=$function_exit
if [ $proceed = 0 ]
then
echo "db_mount_restrict" > $CLONE_CONTROL_FILE
else
exec_stat=2
fi
elif [ $proceed = 99 ]
then
echo "Skipping db_shutdown as step already completed" >> $CLONE_LOG
proceed=0
fi

if [ $proceed = 0 ]
then
db_shutdown_end=`date +"%Y:%m:%d %H:%M:%S"`
echo "Completed db_shutdown - Finished: $db_shutdown_end" >> $CLONE_LOG
unset db_shutdown_start db_shutdown_end
check_run db_mount_restrict
else
if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]
then
exec_stat=2
echo "Failed db_shutdown" >> $CLONE_LOG
fi
fi

if [ $proceed = 0 ]
then
db_mount_restrict_start=`date +"%Y:%m:%d %H:%M:%S"`
echo "Running db_mount_restrict - Started : $db_mount_restrict_start" >> $CLONE_LOG
function_exit=1
send_running_clone_status_updates 0 db_shutdown db_mount_restrict
db_mount_restrict
proceed=$function_exit
if [ $proceed = 0 ]
then
echo "db_drop" > $CLONE_CONTROL_FILE
else
exec_stat=3
fi
elif [ $proceed = 99 ]
then
echo "Skipping db_mount_restrict as step already completed" >> $CLONE_LOG
proceed=0
fi

if [ $proceed = 0 ]
then
echo "Completed db_mount_restrict" >> $CLONE_LOG
check_run db_drop
else
if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]
then
exec_stat=3
echo "Failed db_mount_restrict" >> $CLONE_LOG
fi
fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 db_mount_restrict db_drop
db_drop
proceed=$function_exit
if [ $proceed = 0 ]; then echo "db_nomount" > $CLONE_CONTROL_FILE; else exec_stat=4; fi
elif [ $proceed = 99 ]; then echo "Skipping db_drop" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run db_nomount; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=4; echo "Failed db_drop" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 db_drop db_nomount
db_nomount normal
proceed=$function_exit
if [ $proceed = 0 ]; then echo "db_restore" > $CLONE_CONTROL_FILE; else exec_stat=5; fi
elif [ $proceed = 99 ]; then echo "Skipping db_nomount" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run db_restore; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=5; echo "Failed db_nomount" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 db_nomount db_restore
db_restore
proceed=$function_exit
if [ $proceed = 0 ]; then echo "db_startup" > $CLONE_CONTROL_FILE; else exec_stat=6; fi
elif [ $proceed = 99 ]; then echo "Skipping db_restore" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run db_startup; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=6; echo "Failed db_restore" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 db_restore db_startup
db_startup normal $DB_STARTUP_LOG
proceed=$function_exit
if [ $proceed = 0 ]; then echo "db_validate_temp" > $CLONE_CONTROL_FILE; else exec_stat=7; fi
elif [ $proceed = 99 ]; then echo "Skipping db_startup" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run db_validate_temp; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=7; echo "Failed db_startup" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 db_startup db_validate_temp
db_validate_temp
proceed=$function_exit
if [ $proceed = 0 ]; then echo "db_rename_cdb" > $CLONE_CONTROL_FILE; else exec_stat=8; fi
elif [ $proceed = 99 ]; then echo "Skipping db_validate_temp" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run db_rename_cdb; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=8; echo "Failed db_validate_temp" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 db_validate_temp db_rename_cdb
db_rename_cdb
proceed=$function_exit
if [ $proceed = 0 ]; then echo "db_rename_pdb" > $CLONE_CONTROL_FILE; else exec_stat=9; fi
elif [ $proceed = 99 ]; then echo "Skipping db_rename_cdb" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run db_rename_pdb; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=9; echo "Failed db_rename_cdb" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 db_rename_cdb db_rename_pdb
db_rename_pdb
proceed=$function_exit
if [ $proceed = 0 ]; then echo "db_util_file" > $CLONE_CONTROL_FILE; else exec_stat=10; fi
elif [ $proceed = 99 ]; then echo "Skipping db_rename_pdb" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run db_util_file; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=10; echo "Failed db_rename_pdb" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 db_rename_pdb db_util_file
db_util_file
proceed=$function_exit
if [ $proceed = 0 ]; then echo "db_conc_clean" > $CLONE_CONTROL_FILE; else exec_stat=11; fi
elif [ $proceed = 99 ]; then echo "Skipping db_util_file" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run db_conc_clean; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=11; echo "Failed db_util_file" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 db_util_file db_conc_clean
db_conc_clean
proceed=$function_exit
if [ $proceed = 0 ]; then echo "db_autoconfig" > $CLONE_CONTROL_FILE; else exec_stat=12; fi
elif [ $proceed = 99 ]; then echo "Skipping db_conc_clean" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run db_autoconfig; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=12; echo "Failed db_conc_clean" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 db_conc_clean db_autoconfig
db_autoconfig
proceed=$function_exit
if [ $proceed = 0 ]; then echo "db_custom_users" > $CLONE_CONTROL_FILE; else exec_stat=13; fi
elif [ $proceed = 99 ]; then echo "Skipping db_autoconfig" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run db_custom_users; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=13; echo "Failed db_autoconfig" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 db_autoconfig db_custom_users
db_custom_users
proceed=$function_exit
if [ $proceed = 0 ]; then echo "db_custom_directories" > $CLONE_CONTROL_FILE; else exec_stat=14; fi
elif [ $proceed = 99 ]; then echo "Skipping db_custom_users" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run db_custom_directories; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=14; echo "Failed db_custom_users" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 db_custom_users db_custom_directories
db_custom_directories
proceed=$function_exit
if [ $proceed = 0 ]; then echo "ebs_binaries_cleanup" > $CLONE_CONTROL_FILE; else exec_stat=15; fi
elif [ $proceed = 99 ]; then echo "Skipping db_custom_directories" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run ebs_binaries_cleanup; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=15; echo "Failed db_custom_directories" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 db_custom_directories ebs_binaries_cleanup
ebs_binaries_cleanup
proceed=$function_exit
if [ $proceed = 0 ]; then echo "ebs_binaries_download" > $CLONE_CONTROL_FILE; else exec_stat=16; fi
elif [ $proceed = 99 ]; then echo "Skipping ebs_binaries_cleanup" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run ebs_binaries_download; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=16; echo "Failed ebs_binaries_cleanup" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 ebs_binaries_cleanup ebs_binaries_download
ebs_binaries_download
proceed=$function_exit
if [ $proceed = 0 ]; then echo "ebs_binaries_untar" > $CLONE_CONTROL_FILE; else exec_stat=17; fi
elif [ $proceed = 99 ]; then echo "Skipping ebs_binaries_download" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run ebs_binaries_untar; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=17; echo "Failed ebs_binaries_download" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 ebs_binaries_download ebs_binaries_untar
ebs_binaries_untar
proceed=$function_exit
if [ $proceed = 0 ]; then echo "ebs_adcfg_primary_node" > $CLONE_CONTROL_FILE; else exec_stat=18; fi
elif [ $proceed = 99 ]; then echo "Skipping ebs_binaries_untar" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run ebs_adcfg_primary_node; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=18; echo "Failed ebs_binaries_untar" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 ebs_binaries_untar ebs_adcfg_primary_node
ebs_adcfg_primary_node
proceed=$function_exit
if [ $proceed = 0 ]; then echo "ebs_adcfg_secondary_node" > $CLONE_CONTROL_FILE; else exec_stat=19; fi
elif [ $proceed = 99 ]; then echo "Skipping ebs_adcfg_primary_node" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run ebs_adcfg_secondary_node; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=19; echo "Failed ebs_adcfg_primary_node" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 ebs_adcfg_primary_node ebs_adcfg_secondary_node
ebs_adcfg_secondary_node
proceed=$function_exit
if [ $proceed = 0 ]; then echo "ebs_fndcpass" > $CLONE_CONTROL_FILE; else exec_stat=20; fi
elif [ $proceed = 99 ]; then echo "Skipping ebs_adcfg_secondary_node" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run ebs_fndcpass; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=20; echo "Failed ebs_adcfg_secondary_node" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 ebs_adcfg_secondary_node ebs_fndcpass
ebs_fndcpass
proceed=$function_exit
if [ $proceed = 0 ]; then echo "ebs_start_run_admin_server" > $CLONE_CONTROL_FILE; else exec_stat=21; fi
elif [ $proceed = 99 ]; then echo "Skipping ebs_fndcpass" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run ebs_start_run_admin_server; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=21; echo "Failed ebs_fndcpass" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 ebs_fndcpass ebs_start_run_admin_server
ebs_start_run_admin_server
proceed=$function_exit
if [ $proceed = 0 ]; then echo "ebs_context_updates" > $CLONE_CONTROL_FILE; else exec_stat=22; fi
elif [ $proceed = 99 ]; then echo "Skipping ebs_start_run_admin_server" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run ebs_context_updates; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=22; echo "Failed ebs_start_run_admin_server" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 ebs_start_run_admin_server ebs_context_updates
ebs_context_updates
proceed=$function_exit
if [ $proceed = 0 ]; then echo "ebs_soft_link_updates" > $CLONE_CONTROL_FILE; else exec_stat=23; fi
elif [ $proceed = 99 ]; then echo "Skipping ebs_context_updates" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run ebs_soft_link_updates; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=23; echo "Failed ebs_context_updates" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 ebs_context_updates ebs_soft_link_updates
ebs_soft_link_updates
proceed=$function_exit
if [ $proceed = 0 ]; then echo "ebs_autoconfig" > $CLONE_CONTROL_FILE; else exec_stat=24; fi
elif [ $proceed = 99 ]; then echo "Skipping ebs_soft_link_updates" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run ebs_autoconfig; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=24; echo "Failed ebs_soft_link_updates" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 ebs_soft_link_updates ebs_autoconfig
ebs_autoconfig
proceed=$function_exit
if [ $proceed = 0 ]; then echo "ebs_profile_resp_conc_updates" > $CLONE_CONTROL_FILE; else exec_stat=25; fi
elif [ $proceed = 99 ]; then echo "Skipping ebs_autoconfig" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run ebs_profile_resp_conc_updates; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=25; echo "Failed ebs_autoconfig" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 ebs_autoconfig ebs_profile_resp_conc_updates
ebs_profile_resp_conc_updates
proceed=$function_exit
if [ $proceed = 0 ]; then echo "ebs_custom_updates" > $CLONE_CONTROL_FILE; else exec_stat=26; fi
elif [ $proceed = 99 ]; then echo "Skipping ebs_profile_resp_conc_updates" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run ebs_custom_updates; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=26; echo "Failed ebs_profile_resp_conc_updates" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 ebs_profile_resp_conc_updates ebs_custom_updates
ebs_custom_updates
proceed=$function_exit
if [ $proceed = 0 ]; then echo "ebs_stop_run_admin_server" > $CLONE_CONTROL_FILE; else exec_stat=27; fi
elif [ $proceed = 99 ]; then echo "Skipping ebs_custom_updates" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run ebs_stop_run_admin_server; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=27; echo "Failed ebs_custom_updates" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 ebs_custom_updates ebs_stop_run_admin_server
ebs_stop_run_admin_server
proceed=$function_exit
if [ $proceed = 0 ]; then echo "ebs_integrations" > $CLONE_CONTROL_FILE; else exec_stat=28; fi
elif [ $proceed = 99 ]; then echo "Skipping ebs_stop_run_admin_server" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run ebs_integrations; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=28; echo "Failed ebs_stop_run_admin_server" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 ebs_stop_run_admin_server ebs_integrations
ebs_integrations
proceed=$function_exit
if [ $proceed = 0 ]; then echo "ebs_custom_patch_fs_updates" > $CLONE_CONTROL_FILE; else exec_stat=29; fi
elif [ $proceed = 99 ]; then echo "Skipping ebs_integrations" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run ebs_custom_patch_fs_updates; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=29; echo "Failed ebs_integrations" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 ebs_integrations ebs_custom_patch_fs_updates
ebs_custom_patch_fs_updates
proceed=$function_exit
if [ $proceed = 0 ]; then echo "ebs_final_apps_shutdown" > $CLONE_CONTROL_FILE; else exec_stat=30; fi
elif [ $proceed = 99 ]; then echo "Skipping ebs_custom_patch_fs_updates" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run ebs_final_apps_shutdown; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=30; echo "Failed ebs_custom_patch_fs_updates" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 ebs_custom_patch_fs_updates ebs_final_apps_shutdown
ebs_final_apps_shutdown
proceed=$function_exit
if [ $proceed = 0 ]; then echo "db_final_shutdown" > $CLONE_CONTROL_FILE; else exec_stat=31; fi
elif [ $proceed = 99 ]; then echo "Skipping ebs_final_apps_shutdown" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run db_final_shutdown; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=31; echo "Failed ebs_final_apps_shutdown" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 ebs_final_apps_shutdown db_final_shutdown
db_final_shutdown
proceed=$function_exit
if [ $proceed = 0 ]; then echo "db_final_startup" > $CLONE_CONTROL_FILE; else exec_stat=32; fi
elif [ $proceed = 99 ]; then echo "Skipping db_final_shutdown" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run db_final_startup; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=32; echo "Failed db_final_shutdown" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 db_final_shutdown db_final_startup
db_final_startup
proceed=$function_exit
if [ $proceed = 0 ]; then echo "db_final_autoconfig" > $CLONE_CONTROL_FILE; else exec_stat=33; fi
elif [ $proceed = 99 ]; then echo "Skipping db_final_startup" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run db_final_autoconfig; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=33; echo "Failed db_final_startup" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 db_final_startup db_final_autoconfig
db_final_autoconfig
proceed=$function_exit
if [ $proceed = 0 ]; then echo "ebs_final_autoconfig" > $CLONE_CONTROL_FILE; else exec_stat=34; fi
elif [ $proceed = 99 ]; then echo "Skipping db_final_autoconfig" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run ebs_final_autoconfig; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=34; echo "Failed db_final_autoconfig" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
send_running_clone_status_updates 0 db_final_autoconfig ebs_final_autoconfig
ebs_final_autoconfig
proceed=$function_exit
if [ $proceed = 0 ]; then echo "ebs_final_apps_startall" > $CLONE_CONTROL_FILE; else exec_stat=35; fi
elif [ $proceed = 99 ]; then echo "Skipping ebs_final_autoconfig" >> $CLONE_LOG; proceed=0; fi
if [ $proceed = 0 ]; then check_run ebs_final_apps_startall; else if [ $exec_stat -eq 0 ] && [ $proceed -ne 90 ]; then exec_stat=35; echo "Failed ebs_final_autoconfig" >> $CLONE_LOG; fi; fi

if [ $proceed = 0 ]
then
ebs_final_apps_startall_start=`date +"%Y:%m:%d %H:%M:%S"`
echo "Running ebs_final_apps_startall - Started : $ebs_final_apps_startall_start" >> $CLONE_LOG
proceed=1
send_running_clone_status_updates 0 ebs_final_autoconfig ebs_final_apps_startall
ebs_final_apps_startall
proceed=$function_exit
if [ $proceed = 0 ]
then
ebs_final_apps_startall_end=`date +"%Y:%m:%d %H:%M:%S"`
echo "Completed ebs_final_apps_startall - Finished: $ebs_final_apps_startall_end" >> $CLONE_LOG
unset ebs_final_apps_startall_start ebs_final_apps_startall_end
send_running_clone_status_updates 0 ebs_final_apps_startall clone_complete
else
exec_stat=36
fi
elif [ $proceed = 99 ]
then
echo "Skipping ebs_final_apps_startall as step already completed" >> $CLONE_LOG
proceed=0
fi

if [ $proceed = 0 ]
then
clone_completion
exec_stat=0
fi

if [ $exec_stat = 0 ]
then
echo "Clone Completed Successfully - exec_stat=$exec_stat" >> $CLONE_LOG
exit 0
else
echo "Clone Failed - exec_stat=$exec_stat" >> $CLONE_LOG
vigt_fail_run
exit $exec_stat
fi