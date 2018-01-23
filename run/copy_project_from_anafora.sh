while [ -n "$1" ]
do
    case "$1" in
        -d) DATE=$2
            echo "Date: $DATE"
            shift ;;
        -s) SERVER=$2
            echo "Server: $SERVER"
            shift ;;
        -f) FOLDER=$2
            echo "Folder: $FOLDER"
            shift ;;
        *) echo "$1 is not an option" ;;
    esac
    shift
done
scp -r anafora@192.168.31.$SERVER:/home/anafora/anafora-project-root/$FOLDER/ /home/xuhaowen/GitHub/focus/Data/dc_labeled/$FOLDER-$SERVER-$DATE
