#!/bin/bash
#echo $PWD # /home/codelab/ver1
#echo "$2" 2
#echo "$1" bracket
#echo "${0%/*}" /home/codelab/ver1/app/api/grading

if [ "$1" == "" -o "$2" == "" ];then
	echo "Usage: $0 <id>_<username> <id>"
	exit
fi

cd "${0%/*}"

if [ ! -e "$PWD"/src/$1.c ] || [ ! -e "$PWD"/cases/check.sh ] || [ ! -e "$PWD"/cases/case_$2.txt ] || [ ! -e "$PWD"/cases/programs/case_$2 ]; then
	echo "docker run error" > results/result_$1.txt
	exit 1 
fi

docker run --ulimit nofile=50:50 --ulimit nproc=100:100 --rm \
-v "$PWD"/src/$1.c:/home/file/$1.c \
-v "$PWD"/src/Makefile:/home/file/Makefile \
-v "$PWD"/cases/check.sh:/home/file/check.sh \
-v "$PWD"/cases/case_$2.txt:/home/file/case_tmp.txt \
-v "$PWD"/cases/programs/case_$2:/home/file/programs/solution \
-w /home/file \
--user root \
run2 \
bash -c "make -s && ./check.sh $1" \
> results/result_$1.txt
