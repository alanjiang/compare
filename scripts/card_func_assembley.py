# -*- coding: utf-8 -*

import sys
import os
from function_extract import *
#from redistool import *

LEFT_BRACE='{'

RIGHT_BRACE='}'

# 缺陷列表

#方法体中，重复包含接口实现:/Users/source_code/dian-web/src/test/java/com/hanniu/online/test/InitDataTestCase.java
#/dian-web/src/test/java/com/hanniu/online/test/InitDataTestCase.java
#132行开始测试
# 找到和第一个{匹配的}停止读取
#返回一个Tuple (start,end)
#由方法的开始行定位方法的结束行

def getMethodRowRange(code_dic,start):

       braces=[]
       end=readLineByLine(code_dic,start,braces)

       print('==>开始行:{},结束行:{}'.format(start,end))

       return (start,end)


#测试用    
def  testFileMethodRowRange(file,start):


       braces=[] #存储{ } 位置信息，存放Tuple (char,row,flag)
       
       lines = read_file(file) #文件所有的行
       code_dic=getCodeDic(lines)#key:行号,value:行内容字典
       
       getMethodRowRang(code_dic,start)
       
       
#递归,花刮号配对算法主程       
def readLineByLine(code_dic,start,braces):

    last=False
    
    if start > len(code_dic) :

        print('==> 达到最大<===')

        return  start
    else:
       line=code_dic[start].strip()

       if line.strip() == '': #为空行直接读取下一行

           start+=1
           return readLineByLine(code_dic,start,braces)
       else:
      
           #print('next:{}'.format(start))

           #开始处理行
           for char in line: #一个字符一个字符地去读取 

                if char == LEFT_BRACE or char == RIGHT_BRACE  : #仅当符号为{ 或者 } 时执行花刮号配对算法

                   braces=matchBrace(braces,char,start)
                   if len(braces) == 0 : # 发现花刮号的行，处理后出现集合清空的情况，说明已找到方法的最后一行

                      print('==>找到最后一行:{}'.format(start))
                      last=True
                      break
           if last:

               return start
           else :
              start+=1
    
              return readLineByLine(code_dic,start,braces)
   
         
        
# 花刮号配对算法主程
# 当前刮号如果是},判断集合中的未尾Tuple是否是{,若是，称为“配对成功",同时从集合中移除集合中的未尾Tuple元素;
# 当前刮号如果是{,创建一个新的Tuple对象，加到集合中。

def  matchBrace(braces,char,row):

     size = len(braces)
     if size == 0: #第一个{

         braces.append((char,row,0)) #生成一个Tuple，加入集合中
         return braces
     
     tailTuple = braces[size-1]

     if char == RIGHT_BRACE: #当前元素右刮号

        if tailTuple[0] == LEFT_BRACE: # 与未尾元素配对成功

           braces.pop(size-1) #移除未尾元素Tuple
     
        else: #未尾元素未配对

           braces.append((char,row,0))
     else:#当前元素左刮号

           braces.append((char,row,0))

     return braces
          
     

        
    
          






def findMethodFromBody(body):

    return body
    



#多个单词组合

def matchWord(str):


    pattern='(?P<method>(?:ABC|EFG){1})'

    res=re.search(pattern,str)

    if res is not None:

       print(res.group('method'))
    


#从文件中找出所有注释

def findCommentsFromFile(file):

    fopen = open(file, 'r')

    fileread = fopen.read()

    result=re.findall(r'\/\*[\s\S]*?\*\/',fileread,re.M)
    
    for comment in result:

      print('==>comment:{}'.format(comment))
 

#文件为单位提取，方便定位缺陷

def extractFuncFromFile(file) :


       lines = read_file(file) #文件所有的行
       code_dic=getCodeDic(lines)#key:行号,value:行内容字典
       
       print('<===file:{}'.format(file))
       dic_class_body=findClassBody(file)
       
       if  dic_class_body is None:
           
           return
        
       #print('==>body:{}'.format(dic_class_body[file]))
       dic_file_methods=findMethods(dic_class_body[file],file)

       dic_file_methods=injectMethodLineNumbers(file,dic_file_methods)

       #方法体内部有类的接口实现类的方法不能正确识别,需要“花刮号算法"来重新修正,更新方法标记
       
       method_markers=dic_file_methods[file]

      
       size=len(method_markers)
       
       for row in range(0,size):

           tpl=getMethodRowRange(code_dic,method_markers[row].start) # 起始行号Tuple
           method_markers[row].start=tpl[0]
           method_markers[row].end= tpl[1]
           method_markers[row].body=getCodeByRowNumbers(code_dic,tpl[0],tpl[1])

       for methodMarker in method_markers:

           print('==>method:{},body:{}'.format(methodMarker.method,methodMarker.body))
          
       '''
       #start 找出带有参数的方法 
       #private,public,protected
       
       pattern='(?P<method>[\S]+\s*\([\s\S]*\))'

       method_markers=dic_file_methods[file]
       
       method_with_praram_list=[]

      
       
       for methodMarker in method_markers:
          #print('===>methodMarker,method_str:{}'.format(methodMarker.method_str))
         
          method_body=getCodeByRowNumbers(code_dic,methodMarker.start,methodMarker.end)

          print('===>method body:{},start:{},end:{}'.format(method_body,methodMarker.start,methodMarker.end))
           
          #仅识别方法名参数
          #res=re.search(pattern,methodMarker.method_str)
          res=re.search(pattern,methodMarker.method_str)
          if res is None:

             continue
          else:

             methodWithParam=res.group('method')
             methodWithParam=removeUnlessLines(methodWithParam)
             #print('===> 带参数的方法:{}'.format(methodWithParam))
             method_with_praram_list.append(methodWithParam)
        
       #找出带有参数的方法      
       '''
       



#提取函数主程,独立的程序,以文件夹为单位提取
def extractFunc(folder,redis) :

    
    dic={}
    dic=iteratorFolder(folder,dic)
    for k in dic:
       file=dic[k]
       lines = read_file(file) #文件所有的行
       code_dic=getCodeDic(lines)#key:行号,value:行内容字典
       
       print('<===file:{}'.format(file))
       dic_class_body=findClassBody(file)
       #print('==>dic_class_body:{}'.format(dic_class_body))
      
       #print('===>dic_class_body[file]=:{}'.format(dic_class_body[file]))

       if  dic_class_body is None:
           
           continue
       #print('==>body:{}'.format(dic_class_body[file]))
       dic_file_methods=findMethods(dic_class_body[file],file)

       dic_file_methods=injectMethodLineNumbers(file,dic_file_methods)
       #private,public,protected
       pattern='(?P<method>[\S]+\s*\([\s\S]*\))'

       method_markers=dic_file_methods[file]
       
       method_with_praram_list=[]
       for methodMarker in method_markers:
          #print('===>methodMarker,method_str:{}'.format(methodMarker.method_str))
         
          method_body=getCodeByRowNumbers(code_dic,methodMarker.start,methodMarker.end)

          print('===>method body:{}'.format(method_body))
           
          #仅识别方法名参数
          #res=re.search(pattern,methodMarker.method_str)
          res=re.search(pattern,methodMarker.method_str)
          if res is None:

             continue
          else:

             methodWithParam=res.group('method')
             methodWithParam=removeUnlessLines(methodWithParam)
             #print('===> 带参数的方法:{}'.format(methodWithParam))
             method_with_praram_list.append(methodWithParam)
        
             
       
       #writeToList(file, method_with_praram_list, redis)
    
def removeUnlessLines(methodWithParam):

    if methodWithParam.find('~') != -1:

       lines=methodWithParam.split('~')

       for line in lines:

           if line.strip() != '':

              if line.find('(') == -1:

                 methodWithParam=methodWithParam.replace(line,'')
                

    return methodWithParam

if __name__ == "__main__":

    '''
    orgId=sys.argv[1]
    containerId=sys.argv[2]
    project=sys.argv[3]
    '''
    file='/Users/source_code/dian-web/src/test/java/com/hanniu/online/test/InitDataTestCase.java'
    extractFuncFromFile(file)
    #start=132
    #testFileMethodRowRang(file,start)
    
    #folder = '/Users/zhangxiao/Desktop/source/dian-web'
    #redis = getRedis('127.0.0.1',6379,'redis2017',0)
    #extractFunc(folder,redis)
    
    #测试单词匹配
    #matchWord('EGFABC')
    
    #测试文本中的所有注释是否可以被正确提取
    #file='/Users/source_code/dian-web/src/main/java/com/hanniu/dian/config/WebSocketConfig.java'
    #findCommentsFromFile(file)
