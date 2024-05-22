#!/bin/sh
# This shell script run each scenario in molecule directory and store log in log directory
REGEX_PATTERN=""
REPO_BASE_PATH="/root/collections/ansible_collections/dellemc/openmanage"
BASE_CONFIG="/root/collections/ansible_collections/dellemc/openmanage/roles/molecule.yml"
ENV_FILE_PATH="/root/.env.yml"
current_file=$(readlink -f "$0")
current_file_dir=$(dirname "$current_file")
LOGPATH="$current_file_dir/log/"
REPORT_GEN="$current_file_dir/report_generation.py"

DIRECTORY_PATH_LIST="$(find $REPO_BASE_PATH -type d -name molecule)"
DELETE_OLD_LOG="false"

if [ ! -d "$LOGPATH" ]; then
  mkdir -p "$LOGPATH"
fi

if [[ "$DELETE_OLD_LOG" == "true" ]]; then
    find $LOGPATH -type f -name "*.log" -delete
fi

for line in $DIRECTORY_PATH_LIST;
do
    scenariopath="${line%/*}"
    SCENARIOS=$(find "$line" -name molecule.yml)
    ROLENAME="$(basename "$(dirname "$line")")"
    for scenario in $SCENARIOS;
    do
        scenariofullpath="${scenario%/*}"
        each_scenario="${scenariofullpath##*/}"
        absolutelogpath="$LOGPATH$ROLENAME-$each_scenario.log"
        if [[ -z $REGEX_PATTERN ]] || [[ $absolutelogpath =~ $REGEX_PATTERN ]]; then
            echo "Running command: molecule -vvv -e $ENV_FILE_PATH --base-config $BASE_CONFIG test -s $each_scenario > $absolutelogpath";
            (cd "$scenariopath" && molecule -vvv -e "$ENV_FILE_PATH" --base-config "$BASE_CONFIG" test -s "$each_scenario" > "$absolutelogpath");
        fi
    done
done

python $REPORT_GEN
