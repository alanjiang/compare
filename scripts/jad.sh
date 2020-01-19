#/bin/sh
#s1:当前文件夹
#s2:反编译后存放java文件的目录
#s3:classes文件夹
cd $1

./jad  -o -8 -r -d$2 -sjava $3/**/*.class