# -*- coding: utf-8 -*
import difflib
import sys
import argparse
import os
import re
import json

from method_mark import *
from function_extract import *
from redistool import *

FILE_NAME_KEY = 'STAT:fileName' #所有类的键值

FUNCTION_NAME_KEY ='STAT:function'# 所有函数的键值




    

def stat(folder,serviceName,serviceId):
    
    #得到文件夹下所有文件
    files = []
    files = readAllFiles(folder,files)
    file_dic = {} #文件统计字典
    fileNames = []
    #先处理文件
    for file in files:
         
         fileName = getFileName(file)
         fileNames.append(fileName)
         #处理函数
         function_dic=stat_function(file,fileName,serviceName)
         writeToCollection(FUNCTION_NAME_KEY, json.dumps(function_dic)) #写入缓存
         function_dic={}#清空
    file_dic['serviceId'] = serviceId
    file_dic['serviceName'] = serviceName
    file_dic['fileNames'] = fileNames
    writeToCollection(FILE_NAME_KEY, json.dumps(file_dic)) #写入缓存
    file_dic = {} #清空不用的字典
    return 'JOB_DONE'
    

# 1,读文件夹返回一个集合
def readAllFiles(folder,datas):


    fileNames = os.listdir(folder)  # 获取当前路径下的文件名，返回List
    
    for file in fileNames:

        newDir = folder + '/' + file
        
        if os.path.isfile(newDir):  # 如果是文件
            
            if os.path.splitext(newDir)[1] == ".java":  # 判断是否是.java
                datas.append(newDir)
        else:
            readAllFiles(newDir,datas) #如果不是.java文件，递归
    return datas

#2,保存数据之前，清空Set

def clearHistoryDatas(tableName):
    try:
      clearCollection(tableName)
    except Exception as e:
      print(e)
      return 'FAIL'
   
    return 'SUCCESS'
   
#3,逐个文件读取,统计函数,字典保存
def stat_function(file,fileName,serviceName):

    dic = {}
    
    dic['fileName'] = fileName
    dic['serviceName'] = serviceName
   
    
    #获取文件的所有的方法集合
    methods = []
    method_markers = extremelyFindMethod(file)
    
    for mk in method_markers:

        methods.append(mk.method)
        
    dic['functionNames'] = methods

    #print(dic)
    
    

    return dic




#4,读取文件名，包名+文件名
def getFileName(file):

    
    filepath, name = os.path.split(file)
    
    file_desc = open(file, 'r')
   
    lines = file_desc.read().splitlines()
    found = False
    package = ''
    for line in lines:

      if line.strip() == '' or  line.strip().startswith('/') or line.strip().startswith('*'):
         continue
      else:
         #package cn.agilean.gitadapter;
         m = re.match(r'(package\s+[a-zA-Z.]+)',line)
         
         if m is not None:

            #print(m.group())

            found = True 
            package = m.group(0)

            break

    if package.find('package') != -1 :

        package = package.replace('package','').strip()

    print('=>package:{}'.format(package))

    if package != '':
        
       fileName = package+'.'+name
       
    else:
        
       fileName = package+name
       
    file_desc.close()

    return fileName
   
'''

$1=/Users/zhangxiao/agilean/valuekanban/git-adapter-server/scripts
$2=/Library/Frameworks/Python.framework/Versions/3.7
$3={"path":"/Users/zhangxiao/agilean/valuekanban",
"nodes":[
{"serviceId":"16e14643658c42b4a99f72f3689c3e17","serviceName":"nsync-server","folder":"/Users/zhangxiao/agilean/valuekanban/nsync-server"},
...
]
}


'''
    
   
if __name__ == "__main__":


    '''测试单个文件夹统计
    folder = '/Users/source_code/dian-web/src/main/java'
    serviceName='dian2'
    serviceId='20191103'
    stat(folder,serviceName,serviceId)
    '''

    
    
    task_str=sys.argv[1]

    print('==>python accept:{}'.format(task_str))

    #task_str='{"path":"/Users/zhangxiao/agilean/valuekanban","nodes":[{"serviceId":"16e14643658c42b4a99f72f3689c3e17", "serviceName":"nsync-server", "folder":"/Users/zhangxiao/agilean/valuekanban/nsync-server"},{"serviceId":"c4f0e1ec8b2b4cc3b4e8db2d585de63b","serviceName":"nsync-server2","folder":"/Users/zhangxiao/agilean/valuekanban/server"}]}'
    dic=json.loads(task_str)
    
    nodes = []

    for k in dic:
       
       #print('=>key:{},value:{}'.format(k,dic[k])

       if k == 'nodes':

          nodes=dic[k]

          break


    #1,清理旧记录
    clearHistoryDatas(FILE_NAME_KEY)
    clearHistoryDatas(FUNCTION_NAME_KEY)

    #2,依次处理
    for node in nodes:

           print('=>serviceId:{},serviceName:{}, folder:{}'.format(node['serviceId'],node['serviceName'],node['folder']))

           stat(node['folder'],node['serviceName'],node['serviceId'])
