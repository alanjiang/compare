# -*- coding: utf-8 -*

#import zipfile

#引入多线程支持
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED, ALL_COMPLETED,as_completed
import subprocess as sub
import time


import os

import sys

import platform

import shutil

import function_extract as func


import re

MAX_WORKERS = 5

'''
作者：姜鹏
时间：2019/11/27
更新内容： 以相同包名为单位执行反编译，多线程大大缩减反编译的时间
'''



#压缩文件夹

'''
def zipDir(dirpath,outFullName):
    """
    压缩指定文件夹
    :param dirpath: 目标文件夹路径
    :param outFullName: 压缩文件保存路径+xxxx.zip
    :return: 无
    """
    zip = zipfile.ZipFile(outFullName,"w",zipfile.ZIP_DEFLATED)
    for path,dirnames,filenames in os.walk(dirpath):
        # 去掉目标跟路径，只对目标文件夹下边的文件及文件夹进行压缩
        fpath = path.replace(dirpath,'')

        for filename in filenames:
            zip.write(os.path.join(path,filename),os.path.join(fpath,filename))
    zip.close()
'''

'''
src:源文件夹
dest: 目标文件夹
注意：java文件没有放在指定的包中
'''

def  placeJavaFileList(src,dest):

     #print('=>dest:{}'.format(dest))
     dic = {}
     #key: fileName, value:file path
     dic =func.iteratorFolder(src,dic)
     for fileName in dic:
       filePath = dic[fileName]
       if fileName.endswith('.java'):  
         packageName = func.getPackage(filePath) #com.abc.efg
         packageFolder = func.genPath(packageName)
         destFolder = dest+'/src/'+packageFolder+'/'
         if packageFolder != ' ':
            createDir(destFolder)
         else:
            pass
         moveFile(filePath,destFolder)
       

#拷贝文档树，将srcFolder文件夹里的所有内容拷贝至dstFolder文件夹
def  moveFolder(srcFolder,destFolder):
     try:
        shutil.copytree(srcFolder, destFolder, symlinks=False, ignore=None)
     except Exception as e:
       print(e)

#反编译的文件归到包下面
def placeFile(file,dest):
    
    
    className = getFilePath(file)

    #print('className:'+className)
    javaFile = getJava(className)

    #print('java:'+javaFile)
    srcFile = dest+'/'+javaFile

    #print('drcFile:'+srcFile)
    
    packageName = getPackage(srcFile) #com.abc.efg

    #print(' packageName:'+ packageName)

    packageFolder = genPath(packageName)

    #print('==>len:{}'.format(len(packageFolder)))

    destFolder = dest+'/'+packageFolder
    if packageFolder != ' ':
       createDir(destFolder)

    if os.path.exists(srcFile):

        if not os.path.exists(destFolder+'/'+javaFile):
           moveFile(srcFile,destFolder)
    else:

        print('==>warning:{} Not decompiled '.format(srcFile))
        


#将文件移到目标位置

def moveFile(srcFile,destFolder):
    
    if os.path.exists(srcFile): #有源文件才移动

         try:
           
           shutil.move(srcFile,destFolder) 

         except Exception as e:
           print(e)
           #print('<=文件:{}已移动至:{},再次移动文件忽略==>'.format(srcFile,destFolder))


#生成目录
def createDir(path):

   if not os.path.exists(path):
      try:
         os.makedirs(path)
      except Exception as e:
        print('path:{} is already created by other thread ..'.format(path))
          

#生成包路径 com.abc => com/abc
def genPath(filePackageName):

    if filePackageName.find('.') != -1:

        return filePackageName.replace('.','/')

    else:

        return filePackageName

# 寻找文件的下级目录
# filePath=D:/dest/abc/def/A.jsp =>
# parentFolder = D:/dest => abc/def

def findSubPath(filePath,parentFolder):


     parent_path = os.path.dirname(filePath)
     
     sub_path = parent_path.replace(parentFolder,'')

     #print(sub_path)

     return sub_path
     
def getJava(classFile):

    return classFile.replace('.class','.java')


def getFilePath(file):

    filepath, name = os.path.split(file)

    return name


def find_name_repeat_files(filepath,dic):

    fileNames = os.listdir(filepath)  # 获取当前路径下的文件名，返回List
    for file in fileNames:

        newDir = filepath + '/' + file
    
        if os.path.isfile(newDir):

           path,name = os.path.split(newDir)

           if name is None:

               continue
           #print(name)
           if findElement(dic,name):

               count = dic[name][1] + 1

               tpl = dic[name]

               list = tpl[0]

               list.append(newDir)

               dic[name] = (list, count)

           else:

               list = []

               list.append(newDir)
               
               dic[name] = (list,1)
        else:
            
            find_name_repeat_files(newDir,dic)#如果不是.class文件，递归
            
    return dic

def findElement(dic,key):

    for k in dic:

        if k == key:

            return True
    return False



#找出所有的临时文内隐类文件, 集合对象
#替换.back 
def findTempFiles(filepath,datas):

    fileNames = os.listdir(filepath)  # 获取当前路径下的文件名，返回List
    for file in fileNames:

        newDir = filepath + '/' + file
        
     
        # if os.path.isdir(newDir): # 如果是文件夹
        if os.path.isfile(newDir):  # 如果是文件

            oldFile = newDir
            newDir = newDir.replace('.back','')

            os.rename(oldFile, newDir)
            
            if file.find('$') != -1:
                
                datas.append(newDir)
                
        else:
            findTempFiles(newDir,datas)                #如果不是.class文件，递归
    return datas
    
# 同一目录为单位，让多线程以目录为单位处理反编译

#返回一个字典 key:包的绝对路径，value: 存储文件的集合

def eachFileByFolder(filepath,dic):

    
    fileNames = os.listdir(filepath)  # 获取当前路径下的文件名，返回List
    for file in fileNames:

        newDir = filepath + '/' + file
        
        #if os.path.isdir(newDir): # 如果是文件夹
        if os.path.isfile(newDir):  # 如果是文件
             
            if os.path.splitext(newDir)[1] == ".class":  # 判断是否是.class
                
                folder = os.path.dirname(newDir)
                if folder in dic.keys():

                   list = dic[folder]
                   
                else:
                   list = []
                list.append(newDir)
                dic[folder] = list
                     
        else:
            eachFileByFolder(newDir,dic)                #如果不是.class文件，递归
    return dic



def eachFileByFolder_back(filepath,dic):

    
    fileNames = os.listdir(filepath)  # 获取当前路径下的文件名，返回List
    for file in fileNames:

        newDir = filepath + '/' + file
        
        # if os.path.isdir(newDir): # 如果是文件夹
        if os.path.isfile(newDir):  # 如果是文件
             
            if os.path.splitext(newDir)[1] == ".class":  # 判断是否是.class
                
                folder = os.path.dirname(newDir)
                if folder in dic.keys():

                   list = dic[folder]
                   
                else:
                   list = []
                list.append(newDir)
                dic[folder] = list
                     
        else:
            eachFileByFolder(newDir,dic)                #如果不是.class文件，递归
    return dic

#集合datas中存放文件的完整路径
def eachFile(filepath,datas):

    
    fileNames = os.listdir(filepath)  # 获取当前路径下的文件名，返回List
    for file in fileNames:

        newDir = filepath + '/' + file
        
        
        
        # if os.path.isdir(newDir): # 如果是文件夹
        if os.path.isfile(newDir):  # 如果是文件

            # 带$的文件会影响反编译的正确性
            '''
            if file.find('$') != -1:
               if not file.endswith('.back'):
                  os.rename(newDir,newDir+'.back')
            '''
            if os.path.splitext(newDir)[1] == ".class":  # 判断是否是.class
                datas.append(newDir)
        else:
            eachFile(newDir,datas)                #如果不是.class文件，递归
    return datas


#windows version

def decompile_win(datas,src,jartool,dest,compilerChoose):

    
    sysstr = platform.system()
    #jad
    if compilerChoose == 1: 
        #/Users/zhangxiao/agilean/valuekanban/python-anti-compile/scripts/jad/mac/jad -o -8 -r -d/Users/zhangxiao/agilean/valuekanban/python-anti-compile/dest.back/src -sjava /Users/source_code/dian-web/target/classes/**/*.class
        if sysstr == 'Windows':
            cmd=jartool+" -o -8 -r -d"+dest+" -sjava "+src+'/**/*.class'
            print('==>jad command:{}'.format(cmd))
            os.system(cmd)
        else:

           shell="sh "+jartool +" "+os.getcwd()+" "+dest+" "+src
           print('==>jad shell:{}'.format(shell))
           os.system(shell)
    # procycon,需要一个文件一个文件地编译
    elif compilerChoose == 2:
        for file in datas:
          if file.find('$') != -1:
             print('==>跳过临时文件:{}'.format(file))
          else:
             
             cmd=os.getcwd()+"/jre1.8.0_231/bin/java -jar "+jartool+" "+file+" -o "+dest
             #print('--执行pycon shell:{}'.format(cmd))
             #os.system(cmd);
             sub.run(cmd,shell=True)
    #fernflower
    else:

        #print('==>阁下选择了fernflower反编译<===')
        repeats = []
        for file in datas:

          try:
             execFernflowerCmd(file,dest,jartool,repeats)
          except Exception as e:

            print('<==The file is already decompiled by another thred,skip <===')
    
   
#src: classes 文件夹，需要反编译的文件夹
def decompile_linux(datas,src,jartool,dest,compilerChoose):
     
    sysstr = platform.system()
    #jad
    if compilerChoose == 1: 
        #/Users/zhangxiao/agilean/valuekanban/python-anti-compile/scripts/jad/mac/jad -o -8 -r -d/Users/zhangxiao/agilean/valuekanban/python-anti-compile/dest.back/src -sjava /Users/source_code/dian-web/target/classes/**/*.class
        if sysstr == 'Windows':
            cmd=jartool+" -o -8 -r -d"+dest+" -sjava "+src+'/**/*.class'
            #print('==>jad command:{}'.format(cmd))
            os.system(cmd)
        else:

           shell="sh "+jartool +" "+os.getcwd()+" "+dest+" "+src
           #print('==>jad shell:{}'.format(shell))
           os.system(shell)
    # pycon,需要一个文件一个文件地编译
    elif compilerChoose == 2:
        for file in datas:
          if file.find('$') != -1:
             print('==>跳过临时文件:{}'.format(file))
          else:

             cmd="java -jar "+jartool+" "+file+" -o "+dest
             #print('--执行pycon shell:{}'.format(cmd))
             #os.system(cmd);
             sub.run(cmd,shell=True)
    #新增 fernflower反编译
    else:
        #print('==>阁下选择了fernflower反编译<===')
        #print('fernflower反编译器正在卖力进行中，请稍候...')
        repeats = []
        
        for file in datas:

            
             try:
                execFernflowerCmd(file,dest,jartool,repeats)
                #print(dest)
             except Exception as e:

               #print(e)
               pass
             
        
        
# 避免多个地方维护命令行
# fernflower命令行
# 多个步骤合并成一个逻辑
# repeats: [] ,存储已经处理过的A$1.class对应的A.class
#A$1.class 先执行，再执行 A.class会反编译不准
#先 com/XXX/A.class 反编译报异常，再com/XXX/A$1.class使用A*.class正确编译，覆盖
#先 com/XXX/A$1.class 正确反编译，重复中加入 com/XXX/A.class,下次遇到com/XXX/A.class跳过反编译

def execFernflowerCmd(file,dest,jartool,repeats):

    #print(type(repeats))

    if repeats:
       for repeat in repeats:

          if repeat == file:

             #print('file:{} already decompiled'.format(file))

             return
   
    cmdFile = getMatchClass (file,'$')
    index = file.find('$')
    if index != -1:
      
        repeatFile = file[:index]+".class"

        repeats.append(repeatFile) 

        
    sysstr = platform.system()

    if sysstr == 'Windows':
         
         cmd = os.getcwd()+"/jre1.8.0_231/bin/java -jar  "+jartool+" -hes=0  -hdc=0 -dgs=1 -din=1 "+ cmdFile+" "+dest
    else:
         cmd = "java -jar  "+jartool+" -hes=0  -hdc=0 -dgs=1 -din=1 "+ cmdFile+" "+dest
         #print(cmd)

    #os.system(cmd)
    sub.run(cmd,shell=True)
    #以文件夹为单位，不存在重复文件名，不需要移到不同的包下面
    #placeFileList(dest)

    
    
# A$1.class 如果反编译了，请不要再反编译A.class 否则会覆盖，报异常,结果不准
def getMatchClass(file,char):

    
    index =  file.find(char)

    if index > 0 :

        return file[:index]+"*.class"
    else:
        return file

   
#反编译主函数
# 使用eachFileByFolder来分组，多线程来执行
#compilerChoose-> 2: procyon,1: jad
def batch_decompile(folder1,folder2,compilerChoose):

    print('===>current path:{}'.format(os.getcwd()))

    current_folder=os.getcwd()
    
    #JAR_TOOL=current_folder+'/procyon-decompiler.jar'
    
    JAR_TOOL=loadTool(compilerChoose)

    dest_folder1=current_folder+'/report/dest1'

    dest_folder2=current_folder+'/report/dest2'
    #print('=>eachFolder1:{}'.format(folder1))

    dic1={}
    
    dic1=eachFileByFolder(folder1,dic1)

    #print('=>eachFolder2:{}'.format(folder2))
    
    print('******开始批量反编译，最大工作线程:{}*******'.format(MAX_WORKERS))
    dic2={}
    dic2=eachFileByFolder(folder2,dic2)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as t:

       all_task = []

       ts = 0
       tol1 = 0
       tol2 = 0

       tol1 = len(dic1)
       tol2= len(dic2)
       tol = tol1+tol2
       print('******总共{}个任务,将耗时3-35分钟左右，具体时间视系统性能，请耐心等待********'.format(tol))
       for key1 in dic1:
            ts+=1
            TEM = 'TM{}'.format(ts)
            datas1 = dic1[key1]
            tol1+= len(datas1)
            
            createDir(dest_folder1+'/'+TEM)
            time.sleep(1.1)
            all_task.append(t.submit(decompileTask,datas1,folder1,JAR_TOOL,dest_folder1,compilerChoose,TEM))

       for key2 in dic2:
            ts+=1
            TEM = 'TM{}'.format(ts)
            datas2 = dic2[key2]
            tol2+= len(datas2)
            createDir(dest_folder2+'/'+TEM)
            time.sleep(1.1)
            all_task.append(t.submit(decompileTask,datas2,folder2,JAR_TOOL,dest_folder2,compilerChoose,TEM))

       count = 0
       tol = tol1+tol2
       print('******总共{}个文件反编译********'.format(tol))
       for future in as_completed(all_task):
           
            data = future.result()
            count+=1
            
            print('完成任务:{}/{}'.format(count,ts))
            
            
       
    print('<====结束线程池批量执行<====')

    #将文件还原到指定的包中 dest_folder1+'/'+TEM, dest_folder2+'/'+TEM
   
    
     
    

#每个线程按不同的包分组执行任务
def  decompileTask(datas,folder,tool,dest,compilerChoose,TEM):

   dest_folder = dest+'/'+TEM

   sysstr = platform.system()
   if  sysstr == 'Windows':
         
        decompile_win(datas,folder,tool,dest_folder,compilerChoose)

   else:
        
        decompile_linux(datas,folder,tool,dest_folder,compilerChoose)

   return 'OK'

def loadTool(compilerChoose):

  current_folder=os.getcwd()
  if compilerChoose == 2: #procyon

      return current_folder+'/procyon-decompiler.jar'
  if compilerChoose == 3:
      return current_folder+'/fernflower.jar'
  sysstr = platform.system()
  if(sysstr =="Windows"):
    print('==>You are using Windows platform<===')
    return current_folder+'/jad.exe'
  elif(sysstr == "Linux"):
    print('==>You are using Linux platform<===')
    return current_folder+'/jad.sh'
  else:
    print('==>You are using Mac platform<===')
    return current_folder+'/jad.sh'






     
    
if __name__ == "__main__":

    '''
    JAR_TOOL=sys.argv[1]
    SRC_FOLDER=sys.argv[2]
    DEST_FOLDER=sys.argv[3]
    print('SRC_FOLDER:{},DEST_FOLDER:{}, JAR_TOOL:{}'.format(SRC_FOLDER,DEST_FOLDER,JAR_TOOL))
    datas=eachFile(SRC_FOLDER)
    print(datas)
    decompile(datas,JAR_TOOL,DEST_FOLDER)
    '''
    #fd1='/Users/zhangxiao/Desktop/temp/old/classes'
    #fd2='/Users/zhangxiao/Desktop/temp/new/classes'
    
    #batch_decompile(fd1,fd2)

    #test eachFile
    '''
    datas=[]
    
    datas=eachFile('/Users/zhangxiao/Desktop/source/差异class/a/classes',datas)
  
    for file in datas:

        print('--file:{}'.format(file))
    '''
    #test find_name_repeat_files
    #dic = {}
    #folder = '/Users/zhangxiao/jd-core/jd-core-maven'
    #find_name_repeat_files(folder,dic)


    #测试placeFile(..)逻辑
    '''

    path = '/sc/dg/A.class'

    fileName = getFilePath(path)

    print('==>fileName:{}'.format(fileName))

    file = '/Users/zhangxiao/Desktop/source/class-old/classes/com/hanniu/dian/controller/newsales/usr/home/NewSalesController.class'
    dest = '/Users/zhangxiao/agilean/valuekanban/python-anti-compile/scripts/report/java/'
    placeFile(file,dest)

    '''
    #找出并恢复.class文件
    '''
    path = '/Users/zhangxiao/Desktop/source/class-old/classes'
    list = [] 
    list = findTempFiles(path,list)

    for item in list:   

        print(item)
    '''

    '''
    dir = '/Users/zhangxiao/Desktop/source/classes-new/classes'

    outFile = '/Users/zhangxiao/Desktop/source/classes-new/class.zip'


    zipDir(dir,outFile)

    print('==>Done<==')
    
    '''

    #测试将反编译的java文件按包移动到dest下级目录
    '''
    dest = '/Users/zhangxiao/Desktop/source/dest'


    placeFileList(dest)

    '''

    #测试
    '''
    file = '/Users/zhangxiao/Desktop/source/class-old/classes/com/hanniu/dian/tools/HttpUtils$1.class'

    
    file = getMatchClass(file,'$')

    print(file)
    '''
    '''
    path = '/Users/zhangxiao/Desktop/source/class-old' 
    datas = []
    findTempFiles(path,datas)

    
   

    path = '/Users/zhangxiao/Desktop/source/classes-new'
    datas = []
    findTempFiles(path,datas)


    path = '/Users/zhangxiao/Desktop/source/simple/class-old'
    datas = []
    findTempFiles(path,datas)

    path = '/Users/zhangxiao/Desktop/source/simple/classes-new'
    datas = []
    findTempFiles(path,datas)
    '''

    #folder1 =  '/Users/zhangxiao/Desktop/source/class-old'

    #folder2 =  '/Users/zhangxiao/Desktop/source/simple/classes-new'

    
    #compilerChoose = 3
    
    #batch_decompile(folder1,folder2,compilerChoose)

    #load_files(folder1)

    #fd1='/Users/zhangxiao/agilean/valuekanban/python-anti-compile/scripts/report/dest1'
    #fd2='/Users/zhangxiao/agilean/valuekanban/python-anti-compile/scripts/report/dest2'

    #placeJavaFileList(fd1)

    #placeJavaFileList(fd2)

    #filePath='D:/dest/abc/def/A.jsp'
    #parentFolder='D:/dest'
    #findSubPath(filePath,parentFolder)
    
   

    
    

                  
