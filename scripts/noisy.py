# -*- coding: utf-8 -*

import difflib
import sys
import argparse
import os
import re

from function_extract import * 



NOISY_STRING_VALUE_OF = 'String.valueOf'


#相同包里面的两个文件
#file1中含有String.valueOf(....) 先去掉String.valueOf(),再找到file2中的匹配
def eleminate_noise (file1,file2):

    lines1  = read_file(file1)
    lines2 = read_file(file2)

    row = 0
    for line1 in lines1:

        row+=1
        found = False
        for line2 in lines2:

            if line1.strip() == line2.strip():

                found = True

                break
        if not found:

            
           if line1.find(NOISY_STRING_VALUE_OF) != -1:

               start_pos = line1.find(NOISY_STRING_VALUE_OF)
               print(line1)
               print('row:{},found start position:{}'.format(row,start_pos))

               print(line1[:start_pos])

               #'''
               pattern = re.compile(r'String.valueOf\s*\([\s\S]+\)')

               res = pattern.findall(line1)

               if res:

                  for str in res:

                      print('=>matched:{}'.format(str))
               #'''


# 读取一行字符，找到 valueOf(XXXX) 将 valueOf( ) 去掉，保留XXX
# 算法

def findPos (line,oldStr, newStr):

    return 'OK'




def testFolderRead(folder):


     dic = {}
     dic=iteratorFolder(folder,dic)
     '''
     for key in dic:

         print('=>key:{},value:{}'.format(key,dic[key]))

     '''
     print('==> folder:{},numbers:{}'.format(folder,len(dic)))
      






if __name__ == "__main__":

    #print('=>start<=')

    #file1='/Users/zhangxiao/Desktop/source/report/dest1/CDB/cDB004/CDB004.java'

    #file2='/Users/zhangxiao/Desktop/source/report/dest2/CDB/cDB004/CDB004.java'

    #eleminate_noise(file1,file2)

    folder = '/Users/zhangxiao/Desktop/source/report/dest1'


    
    testFolderRead(folder)



    
