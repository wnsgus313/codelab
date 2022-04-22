#!bin/bash

docker run --ulimit nofile=17:17 --ulimit nproc=100:100 --memory="256m" --rm \
-v $1:/home/file \
-w /home/file \
--user www-data \
run \
bash -c "gcc cfile.c -o file 2> compile_error.txt;
if [ -f file ];then
    if [ -f input1.txt ];then
        trap 'exit' SIGFPE SIGSEGV; timeout 3s ./file < input1.txt > output1.txt;
        signal=\$?;
        if [ \$signal -eq 136 ]; then
            echo 'floating point exception' >&2 > SIGFPE1.txt;
        elif [ \$signal -eq 139 ]; then
            echo 'Segment fault' >&2 > SIGSEGV1.txt;
        elif [ \$signal -eq 124 ]; then
            echo 'Time out' >&2 > Timeout1.txt;
        fi
    fi
    if [ -f input2.txt ];then
        trap 'exit' SIGFPE SIGSEGV; timeout 3s ./file < input2.txt > output2.txt;
        signal=\$?;
        if [[ \$signal -eq 136 ]]; then
            echo 'floating point exception' >&2 > SIGFPE2.txt;
        elif [[ \$signal -eq 139 ]]; then
            echo 'Segment fault' >&2 > SIGSEGV2.txt;
        elif [ \$signal -eq 124 ]; then
            echo 'Time out' >&2 > Timeout2.txt;
        fi
    fi
    if [ -f input3.txt ];then
        trap 'exit' SIGFPE SIGSEGV; timeout 3s ./file < input3.txt > output3.txt;
        signal=\$?;
        if [[ \$signal -eq 136 ]]; then
            echo 'floating point exception' >&2 > SIGFPE3.txt;
        elif [[ \$signal -eq 139 ]]; then
            echo 'Segment fault' >&2 > SIGSEGV3.txt;
        elif [ \$signal -eq 124 ]; then
            echo 'Time out' >&2 > Timeout3.txt;
        fi
    fi
    if [ -f input4.txt ];then
        trap 'exit' SIGFPE SIGSEGV; timeout 3s ./file < input4.txt > output4.txt;
        signal=\$?;
        if [[ \$signal -eq 136 ]]; then
            echo 'floating point exception' >&2 > SIGFPE4.txt;
        elif [[ \$signal -eq 139 ]]; then
            echo 'Segment fault' >&2 > SIGSEGV4.txt;
        elif [ \$signal -eq 124 ]; then
            echo 'Time out' >&2 > Timeout4.txt;
        fi
    fi
else
    echo ''
fi"