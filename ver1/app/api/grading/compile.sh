#!/bin/bash
#echo $PWD # /home/codelab/ver1
#echo "$2" 2
#echo "$1" bracket_{id}
#echo $3 Bracket
#echo $4 DS (Lab)
#echo "$PWD_ID" /home/codelab/ver1/app/api/grading/Bracket


if [ "$1" == "" -o "$2" == "" ];then
	echo "Usage: $0 <id>_<username> <id>"
	exit
fi

cd "${0%/*}"

PWD_ID="$PWD"/"$4/$3" # /home/codelab/ver1/app/api/grading/DS/Bracket
echo $PWD_ID

if [ ! -e "$PWD_ID"/src/$1 ] || [ ! -e "$PWD"/check.sh ] || [ ! -e "$PWD_ID"/cases/input.txt ] || [ ! -e "$PWD_ID"/cases/programs/output.txt ]; then
	echo "docker run error" ${3,,} "$PWD_ID"/src/$1 a "$PWD"/check.sh b "$PWD_ID"/cases/input.txt c "$PWD_ID"/cases/programs/${3,,} > $3/results/result_$2.txt
	exit 1 
fi

docker run --ulimit nofile=50:50 --ulimit nproc=100:100 --rm \
-v $PWD_ID/src/$1:/home/file/$1 \
-v $PWD/check.sh:/home/file/check.sh \
-v $PWD_ID/cases/input.txt:/home/file/case_tmp.txt \
-v $PWD_ID/cases/programs/${3,,}:/home/file/programs/solution \
-w /home/file \
--user root \
run2 \
bash -c "./check.sh $1 $2 $3" \
> $4/$3/results/result_$2.txt

# docker run --ulimit nofile=50:50 --ulimit nproc=100:100 --rm \
# -v "$PWD"/src/$1.c:/home/file/$1.c \
# -v "$PWD"/src/Makefile:/home/file/Makefile \
# -v "$PWD"/cases/check.sh:/home/file/check.sh \
# -v "$PWD"/cases/case_$2.txt:/home/file/case_tmp.txt \
# -v "$PWD"/cases/programs/case_$2:/home/file/programs/solution \
# -w /home/file \
# --user root \
# run2 \
# bash -c "make -s && ./check.sh $1" \
# > results/result_$1.txt
