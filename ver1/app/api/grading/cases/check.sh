#!/bin/bash

cd "${0%/*}"

if [ ! -e ./$1 ] || [ ! -e ./programs/solution ] || [ ! -e case_tmp.txt ];then
	echo "error"
	exit
fi

read case_tmp < case_tmp.txt
if [ "${case_tmp}" == "" ]; then
	res_out=`./$1`
	sol_out=`./programs/solution`
	if [ "${res_out}" != "${sol_out}" ];then
		# it means result is different.
		# otherwise, it will echo 'error' to file.
		echo "fail : must ${sol_out} but give ${res_out}"
		exit
	fi
fi

while read case_in
do
	res_out=`echo ${case_in} | ./$1`
	sol_out=`echo ${case_in} | ./programs/solution`
	if [ "${res_out}" != "${sol_out}" ];then
		# it means result is different.
		# otherwise, it will echo 'error' to file.
		echo "fail : must ${sol_out} but give ${res_out}"
		exit
	fi
done < case_tmp.txt

echo "correct"
