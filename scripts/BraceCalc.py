# -*- coding: utf-8 -*

import sys
import os
from function_extract import *
#from redistool import *


    
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
        
       print('==>body:{}'.format(dic_class_body[file]))

        
       dic_file_methods=findMethods(dic_class_body[file],file)

       #dic_file_methods=injectMethodLineNumbers(file,dic_file_methods)

       #方法体内部有类的接口实现类的方法不能正确识别,需要“花刮号算法"来重新修正,更新方法标记
       
       method_markers=dic_file_methods[file]
      
      
       size=len(method_markers)

       tplList=[] #将各个方法起始坐标放在tuple集合中
       print('==>method_markers,size:{}'.format(size))
       for row in range(0,size):
           print('==>method_marker{}',method_markers[row])
           print('==>method_marker,method:{}'.format(method_markers[row].method))
           
           tpl=getMethodRowRange(code_dic,method_markers[row].start) # 起始行号Tuple
           method_markers[row].start=tpl[0]
           method_markers[row].end= tpl[1]
           method_markers[row].body=getCodeByRowNumbers(code_dic,tpl[0],tpl[1])
           tplList.append((method_markers[row].start, method_markers[row].end))# tuple


       #找出重叠Tuple, 即方法体中的接口方法


       overlapList=pickOverlapList(tplList)

       print('===>重叠Tuple:{}'.format(overlapList))
       if len(overlapList) >0 :

           for overlap in overlapList:

              for  index in range(0,size):

                  if method_markers[index].start == overlap[0] and method_markers[index].end == overlap[1]:

                     method_markers.pop(index)
                     print('==>删除重叠 Tuple: {}'.format(overlap))
                     break
               


       #去掉重叠Tuple后
       for methodMarker in method_markers:

           print('==>start:{},end:{},method:{},\n body:{}'.format(methodMarker.start,methodMarker.end,methodMarker.method,  methodMarker.body))
          
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

#直接调用extractFuncFromFile(file)，结构清晰
def extractFuncByFolder(folder) :

    dic={}
    dic=iteratorFolder(folder,dic)
    for k in dic:
       file=dic[k]
       
       extractFuncFromFile(file)     
       
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
    #file='/Users/source_code/dian-web/src/test/java/com/hanniu/online/test/InitDataTestCase.java'
    file='/Users/source_code/dian-web/src/main/java/com/hanniu/dian/websocket/interceptors/MyHandshakeHandler.java'
    extractFuncFromFile(file)
    #start=132
    #testFileMethodRowRange(file,start)
    
    #folder = '/Users/zhangxiao/Desktop/source/dian-web'
    #extractFuncByFolder(folder)
    
    #redis = getRedis('127.0.0.1',6379,'redis2017',0)
    #extractFunc(folder,redis)
    
    #测试单词匹配
    #matchWord('EGFABC')
    
    #测试文本中的所有注释是否可以被正确提取
    #file='/Users/source_code/dian-web/src/main/java/com/hanniu/dian/config/WebSocketConfig.java'
    #findCommentsFromFile(file)
