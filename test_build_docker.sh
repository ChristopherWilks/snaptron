#builds, deploys, and runs a Snaptron server w/ Apache frontend docker container using the "test" (srav2-based) compilation
#requires that Docker be installed already and that ports 21656 and 2080 are not being used on localhost

#requires a full path to a directory where the "test" compilation's data will be stored
#this will be mounted into the Docker container but will persist between container runs
data_dir=$1

bdir=$(dirname $0)
echo $bdir
if [[ -z $data_dir ]]; then
    echo "MUST pass in the full path to a directory where the "test" compilation data will be persisted across docker runs!\n"
    exit
fi

/bin/bash -x ${bdir}/build_docker.sh
/bin/bash -x ${bdir}/deploy_docker.sh $data_dir test
/bin/bash -x ${bdir}/run_docker.sh $data_dir test
