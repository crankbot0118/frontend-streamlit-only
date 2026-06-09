#!/bin/sh
# Shared argument validation for VIGT clone shell scripts.
# Prevents path traversal when sourcing instance env files.

vigt_validate_dbname()
{
    case "$1" in
        ""|*[!a-zA-Z0-9_-]*|*..*)
            echo "Invalid dbname: $1"
            exit 1
            ;;
    esac
}

vigt_validate_clone_run_id()
{
    case "$1" in
        ""|*[!0-9]*)
            echo "Invalid clone_run_id: $1"
            exit 1
            ;;
    esac
}

vigt_validate_shell_args()
{
    vigt_validate_dbname "$1"
    vigt_validate_clone_run_id "$2"
}
