# -*- coding: utf-8 -*-
import difflib
import sys
import argparse
import os
import re
from method_mark import *
from htmltool import *
from batch_decompiler import *


#from redistool import *

'''
@ Author: 姜鹏 jiangpenghnlg@126.com 
  Date: 2019/10/24
  Note: 先去掉所有空行、注释行后再找到第一个{作为类的内容体、再正则匹配所有的完整方法、带参数方法、使用花括号匹对算法作为寻找方法体起始行
'''

#防止递归深度超过最大1000
sys.setrecursionlimit(1000000)

LINE_SHIFT='~'# 换行符
SHIFT='\n'
TAB='\t'

global_removed_methods={}#相对于旧的版本移除的方法(旧的类中有的方法，新的类中没有), k=文件路径，value:[]
global_added_methods={}  #新的类中有的方法旧的类中没有 
global_added_class=[] # 旧版本中缺少的文件,新增文件
global_removed_class=[]#旧版本中有的文件，新版本中删除

global_diff_class_num = 0
global_diff_method_num = 0

total_method_number=0
total_class_number=0   #总共的类

total_master_class_num=0 #master分支JAVA文件总数
LEFT_BRACE='{'

RIGHT_BRACE='}'

# 缺陷列表: 方法体中存在接口实现类的方法，需要去掉

#(120,127), [(110,138),(120,127) ...] 很显然，(120,127) 处于 (110,138) 内部，是接口实现类的方法，需要找出来

def pickOverlapList(tplList):

    overlapList=[]
    
    for t in tplList:

        if pickOverlap(tplList,t):

           overlapList.append(t)

    return  overlapList


def  pickOverlap(tplList, tpl):

    found=False
    for t in tplList:

        if tpl[0] > t[0] and tpl[1] < t[1]:

            found=True
            return found
  
    return found



#方法体中，重复包含接口实现:/Users/source_code/dian-web/src/test/java/com/hanniu/online/test/InitDataTestCase.java
#/dian-web/src/test/java/com/hanniu/online/test/InitDataTestCase.java
#132行开始测试
# 找到和第一个{匹配的}停止读取
#返回一个Tuple (start,end)
#由方法的开始行定位方法的结束行

def getMethodRowRange(code_dic,start):

       braces=[]
       end=readLineByLine(code_dic,start,braces)

       #print('==>开始行:{},结束行:{}'.format(start,end))

       return (start,end)


#测试用    
def  testFileMethodRowRange(file,start):


       braces=[] #存储{ } 位置信息，存放Tuple (char,row,flag)
       
       lines = read_file(file) #文件所有的行
       code_dic=getCodeDic(lines)#key:行号,value:行内容字典
       
       getMethodRowRange(code_dic,start)
       

            
#递归,花刮号配对算法主程       
def readLineByLine(code_dic,start,braces):
    #print('==code_dic[start]:{}'.format(code_dic[start]))
    last=False
    
    if start > len(code_dic) :
       
        #print('==> 达到最大<===')

        return  start
    else:
       line=code_dic[start].strip()
       
       #if line.strip() == '' or line.strip().startswith('/') or line.strip().startswith('*'): #注释、为空行直接读取下一行

       #    start+=1
       #    return readLineByLine(code_dic,start,braces)
       #else:
      
           #print('next:{}'.format(start))

       #开始处理行
       for char in line: #一个字符一个字符地去读取 

                if char == LEFT_BRACE or char == RIGHT_BRACE  : #仅当符号为{ 或者 } 时执行花刮号配对算法

                   braces=matchBrace(braces,char,start)
                   if len(braces) == 0 : # 发现花刮号的行，处理后出现集合清空的情况，说明已找到方法的最后一行

                      #print('==>找到最后一行:{}'.format(start))
                      return start

       start+=1
       last = (start >= len(code_dic))               
       if last:

               return start
       else :

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
     
        else: #未尾元素tailTuple[0] 为 } ,与char未配对

           braces.append((char,row,0))
     else:#当前元素左刮号

           braces.append((char,row,0))

     return braces
          

# 读取文件所有的行,去掉所有的注释干扰

def read_file(file_name):
    fopen = open(file_name, 'r', encoding='utf-8')
    text = fopen.read()
    text=removeComments(text)
    fopen.close()
    #start测试用
    #fo = open("/Users/zhangxiao/agilean/valuekanban/python-anti-compile/scripts/test.java", "w")
    #fo.write(text)
    #fo.close()
    #end测试用
    return text.splitlines()

#不去注释读取    
def read_file_with_comments(file_name):
    try:
        file_desc = open(file_name, 'r',encoding='utf-8')
        # 读取后按行分割
        text = file_desc.read().splitlines()
        file_desc.close()
        return text
    except IOError as error:
        print(error)
        #sys.exit()


#获取文件带完整包名的文件名
def getPackageName(file):

    
    filepath, name = os.path.split(file)
    
    file_desc = open(file, 'r',encoding='utf-8')
   
    lines = file_desc.read().splitlines()
    found = False
    package = ''
    for line in lines:

      if line.strip() == '' or  line.strip().startswith('/') or line.strip().startswith('*'):
         continue
      else:
         #package cn.agilean.gitadapter;
         pattern = re.compile(r'(package\s+[a-zA-Z0-9\.]+)')
         m = pattern.search(line)
         
         if m is not None:

            #print(m.group())

            found = True 
            package = m.group(0)

            break

    if package.find('package') != -1 :

        package = package.replace('package','').strip()

    #print('=>package:{}'.format(package))
    file_desc.close()
    if package != '':
        
       return package+'.'+name
       
    else:
        
       return name
       


#获取文件完整包
def getPackage(file):

    
    filepath, name = os.path.split(file)

    print('==>filepath:{},name:{}'.format(filepath,name))
    file_desc = open(file, 'r',encoding='utf-8')
   
    lines = file_desc.read().splitlines()
    found = False
    package = ''
    for line in lines:

      if line.strip() == '' or  line.strip().startswith('/') or line.strip().startswith('*'):
         continue
      else:
         #print(line+'\n')
         pattern = re.compile(r'(package\s+[a-zA-Z0-9\.]+)')
         #m = re.match(r'+(package\s+[a-zA-Z.0-9]+)',line)
         m = pattern.search(line)
         if m is not None:

            print(m.group())

            found = True 
            package = m.group(0)

            break

    if package.find('package') != -1 :

        package = package.replace('package','').strip()

    #print('=>package:{}'.format(package))

       
    file_desc.close()

    return package


 # 比较两个文件并把结果生成一份html文本、相似度、差异行位置
 # 修复重名文件覆盖BUG
def compare_file(file1, file2,result_folder,diff_html_file):
    global global_diff_class_num
    
    #print ("正在比较文件{0} 和 {1}".format(file1, file2))
    ratios = {}
    differences={}
    if file1 == "" or file2 == "":
        print('文件路径不能为空：第一个文件的路径：{0}, 第二个文件的路径：{1} .'.format(file1, file2))
        sys.exit()
    
    fileName=getFileName(file1)
    fullFileName = getPackageName(file1)
    #print("fileName:{0}".format(fileName))
    text1_lines = read_file(file1)
    text2_lines = read_file(file2)

    
    
    diff = difflib.HtmlDiff()    # 创建HtmlDiff 对象
    content = diff.make_file(text1_lines, text2_lines)  # 通过make_file 方法输出 html 格式的对比结果
    # 将结果写入到result文件中
    result=result_folder+'/'+fullFileName+'.html'
    try:
        with open(result, 'w',encoding='utf-8') as result_file:
            result_file.write(content)
            #print("==========> Successfully Finished\n")
    except IOError as error:
        print ('写入html文件错误：{0}'.format(error))

    
    #相似度
    '''
    with open(ratio_file,'a') as rtfile:

        s = difflib.SequenceMatcher(None, text1_lines, text2_lines)
        radio=s.ratio()

        #rtfile.write('文件:{}与文件{}相似度:{}\n'.format(file1,file2,radio))

        ratios[file1]=str(radio)
    '''
    #比较差异行的位置

    diffs = findDiffLines(text1_lines, text2_lines)

    #html结果文件
    with open(diff_html_file,'a',encoding='utf-8') as diffFile:

      if len(diffs) == 0:

        #diffFile.write('文件:{}与文件{}没有差异行号\n'.format(file1,file2))
        #print('文件:{}与文件{}没有差异行号\n'.format(file1,file2))
        pass

      else:
        
        global_diff_class_num+=1
        count=0
        size=len(diffs)
        #将diffs排序
        diffs.sort()
        diff_str=''
        for df in  diffs:
            count+=1
            if count == size:
               diff_str+=str(df)
            else:
               diff_str+=str(df)+','
            
            
        differences[genLink(file1)]=diff_str

      #开始写入html报告
      write_table_td(diffFile,differences)

      return len(diffs) == 0 

      '''
      ths=['类名','相似度']
      write_table_th(diffFile,'类文件比较相似度',ths)
      write_table_td(diffFile,ratios)
      write_table_tail(diffFile)
      '''
def genLink(filepath):

    print('==>filepath:{}'.format(filepath))
    path, fileName = os.path.split(filepath)

    packageName = getPackage(filepath)

    if packageName == '':

        link = fileName+".html"

        
    else:
       link = packageName+"."+fileName+".html"
      
    return "<a href=\"./"+link+"\" target=\"_blank\">"+filepath+"</a>"
    
#比较方法升级 2019/12/03  
def compare_methods(file1,file2,diff_html_file):

   global total_method_number
   global global_diff_method_num
   #dic_class_body_1 = findClassBody(file1) # 文件file1方法体,key=file, value=class body

   #dic_class_body_2 = findClassBody(file2)

   #if dic_class_body_1 is None or dic_class_body_2 is None:
   #   print('文件:{},没有方法体\n\t'.format(file1))
   #   return

   dic_file_methods_1={}

   dic_file_methods_2={}

   #dic_file_methods_1:高可用的文件标记字典,key:文件路径,value: MethodMarker[]
   '''#老逻辑
   #file1
   dic_file_methods_1=findMethods(dic_class_body_1[file1],file1)

   dic_file_methods_1=injectMethodLineNumbers(file1,dic_file_methods_1)

   #file2
   dic_file_methods_2=findMethods(dic_class_body_2[file2],file2)

   dic_file_methods_2=injectMethodLineNumbers(file2,dic_file_methods_2)
   
   #老逻辑
   '''
   dic_file_methods_1[file1]=extremelyFindMethod(file1)
   dic_file_methods_2[file2]=extremelyFindMethod(file2)
       
   #dic_class_body_1={} #清空对象
   #dic_class_body_2={}
   
   
   #代码行字典,可以拿到任意两个整数之间的所有行，即函数体内容
   lines1 = read_file(file1) #文件所有的行
   code_dic1=getCodeDic(lines1) #文件所有的行字典，key:行号,value:行内容

   lines2 = read_file(file2) 
   code_dic2=getCodeDic(lines2) #文件所有的行字典，key:行号,value:行内容

   markers1=dic_file_methods_1[file1]
   total_method_number+=len(markers1)
   markers2=dic_file_methods_2[file2]

   diff_funcs={} #函数差异字典

   with open(diff_html_file,'a',encoding='utf-8') as diff_file:
       
       for marker1 in markers1:#旧版本
          found = False
          for marker2 in markers2:#新版本
             if marker1.method == marker2.method:
                found = True
                #不再使用start,end来比较
                content1=marker1.body
                content2=marker2.body
                if not compare_method_content(content1,content2) :
                   #print('==>difference,method=>{}, body1:{}, body2:{}'.format(marker1.method,content1,content2))
                   #diff_file.write('文件:{},方法:{}有差异\n\t'.format(file1,marker1.method))
                   diff_funcs[genLink(file1)]=marker1.method
                break
          if not found:
             #print('文件:{},方法:{}在比较的文件中没有找到\n\t'.format(file1,marker1.method))
             global_removed_methods[file1]=marker1.method




       #找出新增的方法

       for marker2 in markers2:#新版本
          found = False
          for marker1 in markers1:#旧版本
             if marker1.method == marker2.method:
                found = True
                break
          if not found:
            
             global_added_methods[file2]=marker2.method

       #写入差异内容
       write_table_td(diff_file,diff_funcs)

       global_diff_method_num+=len(diff_funcs)#累加变更的函数

   
def compare_method_content(content1, content2 ):

    if content1.strip() == content2.strip() :
       return True
    else:
        #print('---Diff method content1:{}'.format(content1))
        #print('---Diff method content2:{}'.format(content2))
    
        return False
    
#直接行与行比较,需要正反比较      
def findDiffLines(lines1,lines2):

    rows = 0 #行号

    diffs = [] #统计不同行的集合

    #print('===>正向比较<===')
    
    for line1 in lines1:

      
      rows+=1

      
      matched=False
    
      for line2 in lines2:
       
        if line1 == line2 :

          matched=True
          break
      if matched is False :

        #print('===>Foud difference<==={},{}',line1,line2)
        diffs.append(rows)

    rows = 0

    #print('==> 反向比较 lines1,lines2,{},{}'.format(len(lines1),len(lines2)))
    
    for line2 in lines2:

      rows+=1

      #print('rows:{}'.format(rows))

      matched=False

     
    
      for line1 in lines1:

         if line2 == line1 :
            matched = True
            break
        
      if matched is False:

        #print('===>Foud difference<==={},{}',line1,line2)
          
        diffs.append(rows)

        
    
    return removeRepeat(diffs)






    




#集合去重
def removeRepeat(collection):

    if collection is None or len(collection) ==0 :

        return collection
    else:

        return list(set(collection))
    

def getFileName(file_path):
    

    (filepath, tempfilename) = os.path.split(file_path)

    #print("==>filepath:{0}".format(filepath))
    (filename, extension) = os.path.splitext(tempfilename)

    return filename


def getFullFileName(file_path):

    (filepath, tempfilename) = os.path.split(file_path)

    #print("==>filepath:{0}".format(filepath))
    (filename, extension) = os.path.splitext(tempfilename)

    return filename+extension;



'''
 dic, 字典,key:文件名，value:文件路径,递归找出文夹下所有的 java文件
'''
def iteratorFolder(filepath,dic):

    
    fileNames = os.listdir(filepath)  # 获取当前路径下的文件名，返回List
    for file in fileNames:
        newDir = filepath + '/' + file
        
        # if os.path.isdir(newDir): # 如果是文件夹
        if os.path.isfile(newDir):  # 如果是文件
            #print(newDir)
            #print(os.path.splitext(newDir)[1])
            if os.path.splitext(newDir)[1] == ".java":  # 判断是否是.java
            
               #dic[getFullFileName(newDir)]=newDir
               dic[getPackageName(newDir)] = newDir # 使用包名+文件名避免重名文件
        else:
            iteratorFolder(newDir,dic)                #如果不是.java文件，递归
    return dic;






    
'''
比较两个folder,生成差异报告
'''
    
def genReport(folder1, folder2, result_folder,diff_html_file):
    print('==>旧版本文件夹：{}'.format(folder1))
    print('==>新版本文件夹：{}'.format(folder2))
    global total_class_number
    global total_master_class_num
    #先写入htlm报告的头部信息
    with open(diff_html_file,'w',encoding='utf-8') as diffFile:
         wrtie_header(diffFile)
         #先写生产文件比较行改动结果头部
         ths=['类名','行改动位置']
         write_table_th(diffFile,'生产文件比较行改动结果',ths)
         
    dic1={}

    dic2={}

    dic1=iteratorFolder(folder1,dic1)

    dic2=iteratorFolder(folder2,dic2)

    #开始写入类文件比较行改动结果,旧与新版本比较


    diff_dic = [] #没有差异行的集合
    
    for k1 in dic1:
      total_class_number+=1
      found=False

      for k2 in dic2:
   
        if k1 == k2 : #同样的文件名进行比较

           found=True

           #没有差异行
           if compare_file(dic1[k1],dic2[k2],result_folder,diff_html_file):
               
               diff_dic.append(k1)
               
           break

      
      if found == False:

         #report.write('反编译文件没有找到比较的源码:{0}'.format(k1))
         global_removed_class.append(k1)#旧版本中有的，新版本中没有，从旧版本中移除的类

    #找出新增的文件
    for k2 in dic2:
      total_master_class_num+=1
      found=False

      for k1 in dic1:
   
        if k1 == k2 : #同样的文件名进行比较

           found=True
           break
      if found == False:

           global_added_class.append(k2)#,旧版本中没有的，新的版本中有，新版本中新增的类
           
    #比较完毕写入类文件比较行改动 table tail
    with open(diff_html_file,'a',encoding='utf-8') as diffFile:

          write_table_tail(diffFile)
          ths=['java文件名','发生变更的函数']
          write_table_th(diffFile,'生产java文件比较函数变更记录',ths)

        
    #开始写入函数变更记录
    for k1 in dic1:
      
      for k2 in dic2:
   
        if k1 == k2 : #同样的文件名进行比较

           diff_found = True 
           for item in diff_dic:

              if item == k1:
                  diff_found = False
                  break

           if diff_found: #没有找到差异行不要进行方法比较，节省效率
               
                compare_methods(dic1[k1],dic2[k2],diff_html_file)
           
           break
    
    #比较完毕，生成函数体变更数据 table tail
    with open(diff_html_file,'a',encoding='utf-8') as diffFile:

          write_table_tail(diffFile)
          

   
    with open(diff_html_file,'a',encoding='utf-8') as diffFile:
         
          #生成新增的函数
          ths=['java文件','新增的函数']
          write_table_th(diffFile,'master版本新增函数',ths)
          write_table_td(diffFile,global_added_methods)
          write_table_tail(diffFile)
          #生成移除方法
          ths=['java文件','删除的函数']
          write_table_th(diffFile,'master版本删除的函数',ths)
          write_table_td(diffFile,global_removed_methods)
          write_table_tail(diffFile)
          
          #生成新增的类
          ths=['master版本新增的java文件']
          write_table_th(diffFile,'master版本新增的java文件',ths)
          write_table_td(diffFile,global_added_class)
          write_table_tail(diffFile)

          #生成删除的类
          ths=['master版本删除的java文件']
          write_table_th(diffFile,'master版本删除的java文件',ths)
          write_table_td(diffFile,global_removed_class)
          write_table_tail(diffFile)

          #总共的类，更新的类，总共的方法，更新的方法

          ths=['生产java文件的总数','更新的java文件总数','生产有变动行的java文件中总共的函数数量','发生更新函数','master版本java文件总数']
          write_table_th(diffFile,'生产java文件和函数更新情况',ths)
          write_table_td_ele(diffFile,total_class_number,global_diff_class_num,total_method_number,global_diff_method_num,total_master_class_num)
          write_table_tail(diffFile)
          
          
    #比较完毕，生成html报告的尾部信息 html tail
    with open(diff_html_file,'a',encoding='utf-8') as diffFile:

         write_tail(diffFile) 


#去掉文本内容的所有注释、\t、空行部分
def removeComments(text):

    #fopen = open(file, 'r')

    #fileread = fopen.read()

    result=re.findall(r'\/\*[\s\S]*?\*\/',text,re.M)

    if result is None :

        return text
    
    for comment in result:

      #print('==>注释部分:{}'.format(comment))

      text=text.replace(comment,'')

    result=re.findall(r'(\/\/.*)',text,re.M)

    if result is None :

        return text
    for comment in result:
       #print('==>注释部分:{}'.format(comment))
       text=text.replace(comment,'')
    #去掉所有的空行

    body=''
    
    for str in text.splitlines():

        if str.strip() != '':
            body=body+str+'\n'
    #去掉\t标识
    body=body.replace('\t','')
    return body



#测试移除注释部分
def testRemoveComments(file):

    fopen = open(file, 'r',encoding='utf-8')

    text = fopen.read()

    text=removeComments(text)

    print('==>移除所有注释后，文件内容：{}'.format(text))
    

#类的内容采用“花括号”算法
#第一个{和最后一个}之间的部分
#提高性能，返回一个Tuple (lines, dic) ,lines: 行数， dic: key，文件, value: 类{}之间的内容
def findClassBody(file):

    dic={}
    
    lines = read_file(file) #文件所有的行,去掉注释后的行
    
    code_dic=getCodeDic(lines)#key:行号,value:行内容字典
    firstLeftBrace=0
  
    for line in lines:
       firstLeftBrace+=1
       if line.strip() == '' or  line.strip().startswith('/') or line.strip().startswith('*'): #注释不处理
           
           continue
       
       if line.find(LEFT_BRACE) != -1:
          #print('==>第一个左括号行号:{},line:{}'.format(firstLeftBrace,line)) 
          break
           
      
    tple=getMethodRowRange(code_dic,firstLeftBrace)

    start=tple[0]
    end=tple[1]

    dic[file]=getCodeByRowNumbers(code_dic,start, end)
   
    return (lines,dic)
    
         


#返回一个类的所有的方法,放在字典中

'''
@ dic_class_body: 存储类的字典,key:文件路径，value: 类的内容

@ 返回：字典，key:文件路径，value:方法内容
@ dic: 高可用的字典,key:文件路径,value: MethodMarker[]
'''
def findMethods(dic_class_body,file) :

    #print('==>解析文件:{}'.format(file))

    #使用非贪婪模式匹配 protected,public,private
    #result=re.findall(r'(p[a-z]{5,8}\s[\s\S\]*?\{[\s\S]*)',dic_class_body.replace('\n',LINE_SHIFT).replace('\t',LINE_SHIFT),re.M)
    result=re.findall(r'(p[a-z]{5,8}\s[\s\S\<>\,@\t\n]*\{)',dic_class_body,re.M)
    print('==>所有的 method {}'.format(result))

    
    dic={} #文件的方法字典,key:文件路径,value: MethodMarker
   

    method_markers=[] #MethodMarker集合
    

    for method_str in result:
        
        
        pattern='(?P<method>[a-zA-Z_.]{1,})\(.*\)'

        res=re.search(pattern,method_str)

        if res is None:

           continue
        
        
        else:
           method=res.group('method')
           method_str_rows=len(method_str.split(LINE_SHIFT))
           #print('==>len:{},lastone:{}'.format(method_str_rows,method_str.split(LINE_SHIFT)[method_str_rows-1]))
           #print('====>method_str:{}'.format(method_str))
           #修复构造函数不能识别的BUG,2019/10/13
           lines = method_str.split(LINE_SHIFT)

           for line in lines:

               if line.strip().endswith(';'):

                   method_str=method_str.replace(line,'')
           
           
           #print('==>result2:{}'.format(method_str))
           
           if (not method_str.replace(LINE_SHIFT,'').strip().endswith('{')) or method_str.replace(LINE_SHIFT,'').strip().find('==') != -1  or method_str.replace(LINE_SHIFT,'').strip().find('!=') != -1  or method_str.replace(LINE_SHIFT,'').strip().find('>=') != -1 or method_str.replace(LINE_SHIFT,'').strip().find('<=') != -1 or  method_str.replace(LINE_SHIFT,'').strip().find('class') !=-1 or method_str.replace(LINE_SHIFT,'').strip().find(';') !=-1 or  ( method_str.replace(LINE_SHIFT,'').strip().find('(') ==-1 or method_str.replace(LINE_SHIFT,'').strip().find(')') ==-1 ):

                print('=>method:{} not valid,ignore'.format(method))

           else :

               methodMarker=MethodMarker(method,method_str,method_str_rows,0,0,'') #方法标记
           
               method_markers.append(methodMarker)
                  
            
    '''           
    pattern='(?P<method>[a-zA-Z_]{1,}\(.*\))'
    for methodMarker in method_markers:

       #print('===>methodMarker,method:{}'.format(methodMarker.method))
       print('===>methodMarker,method_str:{}'.format(methodMarker.method_str))
       #仅识别方法名参数
       res=re.search(pattern,methodMarker.method_str)

       if res is None:

          continue
       else:

          methodWithParam=res.group('method')

          print('===> 带参数的方法:{}'.format(methodWithParam))

        
       #method_str_rows=len(methodMarker.method_str.split(LINE_SHIFT))
       #print('===>methodMarker,method_str size:{}'.format(method_str_rows))
     '''
    
    
    dic[file]=method_markers

    return dic #返回字典





#从方法标记中清除不合法的对象,如：private 开头的行
#返回新的方法标记对象，填充 body,重组method, body
def removeInvalidFunc (methodMarkers,code_dic):

    new_method_markers=[]
    removedElements=[]
    size=len(methodMarkers)

    if size == 0 :

       return removedElements

    for methodMarker in methodMarkers:

        
        
        body=getCodeByRowNumbers(code_dic,methodMarker.start,methodMarker.end)

        lines=body.splitlines()

        length=len(lines)

        invalid=False

        for row in range(0,length):

            if row >0 :

                temline=lines[row]

                if temline.strip().startswith('private'):
                    #print('==>不合法的方法体:line:{},body:{}'.format(temline.strip(),body))
                    invalid=True
                    break


        #method_str

        if invalid == False:
               result = re.findall(r'if\s*\(',methodMarker.method_str.strip())

               #print('===>method_str:{},result:{}'.format(methodMarker.method_str.strip(),result))
               
               if len(result) > 0:
                   invalid=True
                   
                
        if invalid:

            print('===>方法标记：{}不合法，移除'.format(methodMarker.method))
            removedElements.append(methodMarker)
         
        
       
    for ele in removedElements:

        #print(ele)

        methodMarkers.remove(ele)

    #获取方法有可能出错 
    for methodMarker in methodMarkers:
   
         body=getCodeByRowNumbers(code_dic,methodMarker.start,methodMarker.end)
         #mm=MethodMarker(methodMarker.method, methodMarker.method_str, methodMarker.method_str_rows, methodMarker.start, methodMarker.end,body)

         #method start
         pattern='(?P<method>\s+[\s\S]+\(.*\))'
         
          #仅识别方法名参数
         
         res=re.search(pattern,methodMarker.method_str,re.M)

         if res is None:

             continue
         else:

            methodWithParam=res.group('method')
            #需要将 LINE_SHIFT去掉
            methodWithParam=methodWithParam.replace(LINE_SHIFT,'')
            mm=MethodMarker(methodWithParam, methodMarker.method_str, methodMarker.method_str_rows, methodMarker.start, methodMarker.end,body)
            new_method_markers.append(mm)
         #method end

    
         
         
    methodMarkers=[]

    return new_method_markers

#返回临时字典，key: 代码行数 , value: 代码行
#lines: 文件所有的代码行
def  getCodeDic(lines):

     dic={}
     count=0
     for line in lines:
        count+=1
        dic[count]=line
        
     return dic
        

#dic: 存储代码行的字典
#返回[start,end]区间的所有行
def getCodeByRowNumbers(dic,start, end):

   
    str=''
    while start<=end:

      try:
        str=str+dic[start]+'\n'
        start+=1
      except KeyError:
        return str  
    return str
   

def checkInvalidMethod(method_str):

    if method_str.strip() == '':

       return True
    for str in method_str:

        if str.strip() == '':

          continueˉ
        if str.strip().endswith(';') or str.strip().find('||') !=-1 or str.strip().find('&&') !=-1 :

           return True


#构造函数正则         
def testConstuctFunc(file):
    tpl=findClassBody(file)#返回一个Tuple(lines,dic)
    lines=tpl[0] #避免多次读文件
    dic_class_body=tpl[1]
    body=dic_class_body[file]
    result=re.findall(r'((?:public|private){1}\s+[a-zA-Z0-9<>,\s_.@]+\s*\([\s\d\w,<>@\"\(\)=]*\)[\s\S^;]*?\{)',body,re.M)
    
    for method_str in result:

       print(method_str)

#无修饰符函数正则 
def testNonModifierFunc(file):
    tpl=findClassBody(file)#返回一个Tuple(lines,dic)
    lines=tpl[0] #避免多次读文件
    dic_class_body=tpl[1]
    body=dic_class_body[file]
    result=re.findall(r'((?:^public^private[A-Z]){1}[a-zA-Z0-9<>,_]{1,}\s*\([\s\d\w,<>@\"\(\)=]*\)[\s\S^;]*?\{)',body,re.S)

    print(result)

#新增方法体变量搜集
    
def  extremelyFindMethod(file):

    
    method_markers=[] #方法标记集合
    
    tpl=findClassBody(file)#返回一个Tuple(lines,dic)

    lines=tpl[0] #避免多次读文件
    dic_class_body=tpl[1]
    body=dic_class_body[file]

    code_dic=getCodeDic(lines) #key:行号,value:行内容,字典
    
    

    if body.strip() == '' :

       return  method_markers
    
    #2019/10/25 无修饰符的函数: (?:void|[a-zA-Z<>,0-9_.\s]+){1}\s+[a-zA-Z0-9<>,_.@]+\s*\([\s\d\w,<>@\"\(\)=]*\)
    #修复正则：方法返回类型中空格识别不到
    
    result=re.findall(r'((?:public|private|protected|final){1,2}\s+(?:static|synchronized)?\s*[a-zA-Z<>0-9,.@]*\s*(?:void|[a-zA-Z<>,0-9_.]+){1}\s+[a-zA-Z0-9<>,_.@]+\s*\([\s\d\w,<>@\"\(\)=]*\)[\s\S^;]*?\{)',body,re.M)

    #print('===>加入构造函数<====')
    result2=re.findall(r'((?:public|private){1}\s+[a-zA-Z0-9<>,\s_.@]+\s*\([\s\d\w,<>@\"\(\)=]*\)[\s\S^;]*?\{)',body,re.M)
    result=result+result2

    result=removeRepeat(result)
    
    dic={} #文件的方法字典,key:文件路径,value: MethodMarker
   
    
    method_markers=[] #MethodMarker集合
    
    method_str_list=[]
    method_list=[]

    #print('=====Type====:{}'.format(type(result)))
    
    for method_str in result:
        
        res = re.findall(r'if\s*\(|catch\s*\(|for\s*\(|new\s+',method_str.strip())
        #print('**************method_str:{}'.format(method_str))
        #print('===>method_str:{},res:{}'.format(method_str,res))
               
        if len(res) > 0:
        
           continue

        #if checkInvalidMethod(method_str):
        #    continue
        #print('==>valid method_str:{}'.format(method_str))
        method_str_list.append(method_str)
        #方法正则
        #2019/10/24 正确版本,让方法method正则与完整方法method_str对应
        #res=re.findall(r'([a-zA-Z0-9<>,_.@\s]+\s*\([\s\d\w,<>@\"\(\)=]*\))',method_str.strip(),re.M)

        res=re.findall(r'([a-zA-Z0-9._]+\s*\([\s\d\w,<>@\"\(\)=]*\))',method_str.strip(),re.M)
        
        if res is not None:

           for method in res:

               #print('==>method:{}'.format(method))
               if method_str.strip().find(method.strip()) != -1: #只取一个正确的方法
                   method_list.append(method)
                   break
               
               

    #处理一个文件的所有的方法
    size1=len(method_str_list)
    size2=len(method_list)
    print('==>file:{},method size:{}, method_str size:{}<=='.format(file,size1,size2))
    '''
    for mstr in method_str_list:

        print('==>method_str:{}'.format(mstr))

    for md in method_list:

        print('==>method:{}'.format(md))
    '''
    if size1 == 0:

        return  method_markers
              
    if size1 == size2: #正常

        tplList=[]

        for index in range(0,size1): #遍历方法集合

           #print('==>method_str:{},size: {}'.format( method_str_list[index],len(method_str_list[index].splitlines())))
           #method_markers.append(MethodMarker(method_list[index], method_str_list[index], len(method_str_list[index].splitlines()), 0, 0,'') )
           #找到文件的起始行
           match_rows = []

           #找到方法的整个区间
           
           
           match_rows=deepVisit(lines,0,0,method_str_list[index].splitlines(), match_rows)

           
           #print('==>****match_rows:{},method_str size:{}'.format(match_rows,len(method_str_list[index].splitlines())))
           
           if len(match_rows) > 0:
               
               start_row=match_rows[0]
               #根据方法的第一行“花括号”配对方法找最后一行的行号位置
               row_range=getMethodRowRange(code_dic,start_row) #由方法的第一行得到一个Tuple起始行
               tplList.append(row_range)
               method_body=getCodeByRowNumbers(code_dic,row_range[0], row_range[1])
               variables = []
               params = []
               method_no_param = ''
               method_markers.append(MethodMarker(method_list[index], method_str_list[index], len(method_str_list[index].splitlines()), row_range[0], row_range[1],method_body,variables,params,method_no_param) )

               #print('method :{} \n body:{}'.format( method_list[index],  method_body))
               
           else :

               print('>>>Warning:file:{} 匹配行集合为0, method_str:{}'.format(file,method_str_list[index]))


        
        # Tuple坐标去除方法内部嵌套的函数

        
        ########## 开始片理重叠区域  #######
        overlapList=pickOverlapList(tplList)


        mmk_size=len(method_markers)
        overLapMakers=[]
        
        for point in range(0,mmk_size):

            maker= method_markers[point]

            for overlap in overlapList:

                if overlap[0] == maker.start and overlap[1] == maker.end:

                   

                    overLapMakers.append(maker)
                    
                    break

        if len(overLapMakers) > 0:
            
           for olpMK in overLapMakers:

                print('==>删除重叠区域函数：{} '.format(olpMK.method))

                method_markers.remove(olpMK)
            
        #print('==>重叠区域函数处理完毕<=====')

         ##########结束片理重叠区域  ################
        
        #print('===>找到函数:{}个,清单:\n'.format(len(method_markers)))
        
    
        size = len(method_markers) 
        for index in range(0,size): #遍历方法集合

           mmk = method_markers[index]

           #method_body: 方法体中找出variables, {('a','int','inner'),('b','String','global'),('c','Date','global')}
           set = findVariables(mmk)
           params = [] 
           #print('=>set:{}'.format(set))
           #获取方法的参数字符串
           params = get_method_param(mmk.method_str)
           #为避免同名不同参函数混淆，需要将参数处理成对象集合
           if params != '' :
               
               variable_collection = reset_method_param_variables(params)
               
               method_no_param = mmk.method_str.replace(params,str(variable_collection))
               
           else:
               
               method_no_param = mmk.method_str
               
           method_markers[index]= MethodMarker(mmk.method, mmk.method_str, mmk.method_str_rows, mmk.start, mmk.end,mmk.body,set,params,method_no_param) 


        #遍历方法标记集合
        for mmk in method_markers:
            print('start:{},end:{},method_str:{},method_no_param:{},variables:{}'.format(mmk.start,mmk.end,mmk.method_str,mmk.method_no_param,set))
    
        return  method_markers  
          
        
    else: #异常

        print('>>>file:{} 完全方法个数为:{},参数方法个数为:{}'.format(file,size1,size2))

        return  method_markers


#递归查找起始行主程    
def deepVisit(lines,line_start,method_start,method_str_list,rows):

   
    method_size=len(method_str_list)
    
    line_end=len(lines) 
    if method_start == method_size or line_start == line_end:
       #print('达到最大')
       return rows
   
    curr_method_str=method_str_list[method_start]
    
    #y:lines行数
    linenumber=0
    for y in range(line_start,line_end):
           linenumber=y+1
           if lines[y].strip() == curr_method_str.strip(): #找到相等行    
          
                if method_size == 1: # 方法只有一行，直接返回

                   #print('==>just one row<==');
                   rows.append(linenumber)
                   return rows
                else: #方法2行以上
                   
                    if len(rows) == 0: # 集合第一行号
                       #print('===>集合第一行号:y:{},linenumber:{}'.format(y,linenumber))
                       rows.append(linenumber) # 加入集合
                       #继续查找第二个方法位置
                       method_start+=1#下一个方法
                       line_start=y
                       return deepVisit(lines,line_start,method_start,method_str_list,rows)
                       
                    else:#已有匹配的行,方法2个以上
                         
                        #如果当前是行号与rows中未尾的行号不相差1，则清除rows, 从str_start+1位置
                        #diff=line_start-rows[len(rows)-1]
                        diff=linenumber-rows[len(rows)-1]
                        #==line_start:613,rows:[614]
                        #print('==line_start:{},rows:{}'.format(line_start,rows))
                        #print('==linenumber:{},rows:{}'.format(linenumber,rows))
                        if diff == 1: #相差1,正常，查找下一个方法遍历
                            rows.append(linenumber)
                            method_start+=1#方法下一个
                            line_start=y
                            return deepVisit(lines,line_start,method_start,method_str_list,rows)
                       
                        else:#相差不为1:

                           
                           method_start=0#重新开始从第一个方法开始查找
                           line_start=rows[len(rows)-1]
                           
                           rows = []#清空，重新查找
                           return deepVisit(lines,line_start,method_start,method_str_list,rows)
                       
    #循环结束

    return rows

'''

由一个方法体找出所有的变量， (变量类型,名称，'global/inner')
for 循环中的变量

定义变量的部分, Tuple对象，存放在set中

还需要定位set中的变量出现的行位置、以参数|调用|赋值形式出现 [(12, 'param'),(12,'call'), (21,'equal')...]

每个方法的变量集合(排序)
'''

def findVariables (method_marker):

 body = method_marker.body
 hashset = set()
 #print('==>body:{},起始行：{}'.format(method_body,start))
 #先找出所有的函数体内的变量
 for row in body.splitlines():

     #print('start:{},end:{},index:{}'.format(start,end,index))
     #row = code_dic[index]
     #print('=>row:{}'.format(row))
     words = row.split('=');
     #print('==>1,words:{},size:{}'.format(words,len(words)))
     
     if len(words) > 1:

        left_part = words[0]

        left_parts = left_part.strip().split(' ')


        size = len(left_parts)

        #print('==>2,size'.format(size))

        if size > 1:
            
            #print('=>left_parts:{}'.format(left_parts))
  
            if validateVariable(left_parts):

                #print('=>valid:{},size:{}'.format(left_parts,size))
               
                if size == 3: #变量带有修饰
                    
                    hashset.add( (left_parts[2],left_parts[1],None,left_parts[0]) )

                elif size == 2: #无修饰符
                    hashset.add( (left_parts[1],left_parts[0], None,'') )

 #转set为list

 collection = list(hashset)

 collection.sort()
 
 # 再次遍历，找到变量所在的位置和形态(参数传入，调用方法，赋值,需要判断
 row_no = 0 #统计方法的行数
 for row in body.splitlines():

     row_no+=1
     if len(hashset) == 0:

         continue
     else:

        pass 


 return collection

 


CAL_LEFT= '()+-*/%><=,'
CAL_RIGHT ='()+-*/%><=,.'

#row_no: 方法的第几行
#找出一个变量在行中出现的次数,如： (3,1):在第3行中出现了1次
#tem_variable:临时替换变量
def get_variable_state (row,row_no,variable,tem_variable,tpl):

    
    index  =  row.find(variable) 
    size = len(variable)

    if index == -1:
        return tpl
    else:
        #åprint('==>found:{}'.format(row))
        left = row[(index-1):index]
    
        right = row[(index+size):(index+size+1)]

        #判断是否以一个单独的单词出现
        valid = True
        #左右均不为空
        if left != '' and right !='':

           if CAL_LEFT.find(left) != -1 and CAL_RIGHT.find(right) != -1: 
               pass
           else:
               valid = False
        #左右均为空
        elif left == '' and right == '':
            pass
        #左不为空，右为空
        elif left != '' and right == '':
            if CAL_LEFT.find(left) != -1:
               pass
            else:
                valid = False
        elif left == '' and right != '':
            if CAL_RIGHT.find(right) != -1:
               pass
            else:
                valid = False
        else:
            pass
        row = '{}{}{}'.format(row[0:index],tem_variable,row[(index+size):])
        if valid:
            #[(第几行,出现次数),...]
            tpl = (tpl[0],tpl[1]+1)
        
            #print('=>replace row:{}'.format(row))
            return get_variable_state(row,row_no,variable, tem_variable,tpl)
        else:#不合法接着找
            return get_variable_state(row,row_no,variable, tem_variable,tpl)

#得到与变量一样长度的临时变量XXX
def getTemVariable(variable):

   size = len(variable)
   str=''
   for i in range(0,size):
    str+='^'
   return str 
       
        
#依据=隔开后，前半部分以空格隔开部分,
def validateVariable(strs):

    pattern = re.compile(r'([a-zA-Z0-9,<>_\.\?]+)')

    valid = True

    size = len(strs)
    
    for str in strs:

      
      match = pattern.search(str)
     
      if not match:

        valid = False

        break
      else:

        if not match.group(0) == str:

           valid = False
           break
        
    return valid
        

def get_method_param(method_str):

    str = ''
    #method_str='public UserDetails loadUserByUsername(Map<Long,String> map, Map<String,Map<Integer) throws UsernameNotFoundException {'
    
    pattern = re.compile(r'\(([\s\d\w,<>@\"\(\)=]*)\)')

    match = pattern.search(method_str)

    if match:

      #print(match.group(1))
      str = match.group(1)
      
    return str   




#获取一个方法method_str的所有的形参，处理成  ('变量名1','变量类型',[(第几行,出现次数),...],'empty|final')

def get_method_param_variables(method_str):


    str = get_method_param(method_str)

    print('==>获取参数字符串:{}'.format(str))

    commas = find_valid_commas(str)

    print('===>获取逗号集合:{}'.format(commas))

    variables = find_valid_param_variables(str,commas)

    return variables

#参数字符串param,由get_method_param(method_str)获取
def reset_method_param_variables(param):

    collection = []
    commas = find_valid_commas(param)
    variables = find_valid_param_variables(param,commas)

    for tpl in variables:

        collection.append(tpl[1])

    return collection
    

# 找出< 和 > 符号集合，再组装成元组 [ (<,>) ,(<,>) ... ]

def find_angle_barces(str):

    c1 = find_char_position(str,'<',[]) #泛型 < 的边界

    c2 = find_char_position(str,'>',[]) #泛型 > 的边界

    size = len(c1)

    collection = [] 
    for i in range(0,size):

        collection.append( ( c1[i], c2[i] ))

    return collection
    
# 方法参数字符串中有效的字符串集合索引位置

def find_valid_commas(str):

   commas = find_char_position (str,',',[]) # 参数字符串中多少个逗号

   size = len(commas)

   removed_commas = [] 

   if str.find('<') == -1 :# 没有泛型符号

      print('==>没有泛型符号<==, 索引位置:{}'.format(commas))

      return commas
      
   else: # 有泛型符号
    
      angles =   find_angle_barces (str) # 得到一个 (<,>) 元组集合
      
      for i in range(0,size):

          comma = commas[i]

          for angle in angles:
              if comma > angle[0] and comma < angle[1]:
                 removed_commas.append(comma)
                 break
      #删除无用逗号索引
      for cm in  removed_commas:

          commas.remove(cm)

      return commas;
# 从方法参数字符串str中，根据有效的逗号索引位置，组装参数变量元组集合[('变量名', '变量类型', '修饰符'),...] 
def find_valid_param_variables ( str, commas):

   variables = []

   size = len(commas)

   print('commas size:{},commas:{}'.format(size,commas))

   
   
   if size == 0:# 只有一个参数

       comma = assembly_variable_tuple(str)
       variables.append(comma)
   
   else:

       commas.append(0) # 新增一个0, 便于Tuple来获取行
       commas.append(len(str))
       commas.sort()

       tpls = []
       size = len(commas)
       for i in range(0,size-1):

           for j in range (i+1, size):

               if i == 0:
                  tpls.append( (commas[i],commas[j]))
               else:
                 tpls.append( (commas[i]+1,commas[j]))
               

               break
       #由Tuple起始位置来获取各个参数表达式

       for tpl in tpls:

           comma = str[tpl[0]:(tpl[1])]
           
           param = assembly_variable_tuple(comma)

           print('==>param:{}'.format(param))
           variables.append(param)
           
       
   return  variables   
      

       

# param 一个表达式 eg: final String abc
# 泛型变量空格需要处理  ('变量名', '变量类型', '修饰符')
# 由一个参数表达式获取变量Tuple唯一入口 
def assembly_variable_tuple ( param):

    param = param.replace(' ,',',').replace(', ',',').replace(' <','<').replace('< ','<').replace(' >','>').strip()

    array  = param.split(' ')

    if len(array) == 2:

        return (array[1],array[0],'')

    elif len(array) == 3:
       return (array[2],array[1],array[0])
    elif len(array) == 4:
      return (array[3],array[2],array[0]+' '+array[1])
    else:
      print('=== warning: param {} 参数错误'.format(param))
      return None
    
#将反编译的文件读取，写入目标文件
#src_file: 反编译文件
#dest_file: 去掉注释、空行之后的行所入到dest_file文件
def write_tidy_file(src_file,dest_file):

    datas = read_file(src_file) #文件所有的行,去掉注释后的行
    
    fo = open(dest_file, 'w', encoding='utf-8')

    for data in datas:

        fo.write(data+'\n')

    fo.close()



'''

执行查找、判断是否这变量、替换算法主程

row : 反编译文本的行

char: 变量名

返回一个替换的值

'''

# 执行多个替换
#原生子串替换
def find_replace_chars(row,old_char,new_char):

    index = row.strip().find(old_char)
    size = len(old_char)
    if index != -1 :

            row = '{}{}{}'.format(row[0:index],new_char,row[(index+size):])
            return find_replace_chars(row,old_char,new_char)
    else: 
       return row




#查找一个char出现在字符串中索引的位置，放在集合中
# eg: str = 'Map<Long,String> map, Map<String,String> map2'
def find_char_position (str,char,collection):

    
    index  =  str.find(char) 
    size = len(char)
    tem_variable = getTemVariable(char)
    if index == -1:
        return collection
    else:
       collection.append(index)
       new_str = '{}{}{}'.format(str[0:index],tem_variable,str[(index+size):])
       
       return find_char_position (new_str,char,collection)
    
'''
旧的和新的比较,有以下结果：
1) 旧的类中的方法在新的类中找不到：删除

2) 旧的类中的方法在新的类中可以找到，但内容不相同： 修改了

3) 新的类中有的方法在旧的类中没有：新增

'''
if __name__ == "__main__":


    #testFileMethodRowRange(file,18)
   
    #测试移除所有注释函数
    #src_file = '/Users/zhangxiao/agilean/valuekanban/python-anti-compile/scripts/examples/dest2/AdminService.java'
    #extremelyFindMethod(src_file)
    # start 测试将干净文件得写
    #src_file = '/Users/zhangxiao/agilean/valuekanban/python-anti-compile/scripts/examples/dest2/AdminService.java'
    #dest_file ='/Users/zhangxiao/agilean/valuekanban/python-anti-compile/scripts/examples/dest2/AdminService_tidy.java'
    #write_tidy_file(src_file,dest_file)
    # end 测试将干净文件得写
    #testRemoveComments(file)

    '''
    #系统参数传入
    '''
    #result_folder=sys.argv[1]
    #diff_html_file=result_folder+'/report/report.html'
    #folder1=sys.argv[2]
    #folder2=sys.argv[3]
    #生成报告
    #genReport(folder1,folder2,result_folder,diff_html_file)
    #print('<===报告Done==>')
    #file1='/Users/zhangxiao/agilean/valuekanban/agilean-rbac-server/src/main/java/cn/agilean/valuekanban/rbac/controller/UserController.java'
    #file1='/Users/zhangxiao/agilean/valuekanban/server/src/main/java/cn/agilean/valuekanban/security/ApplicationSecurity.java'
    #file2='/Users/zhangxiao/git/python-anti-compile/dest2/cn/agilean/valuekanban/cache/consumer/ContainerCacheConsumer.java'
    #lines1 = read_file(file1)
    #lines2 = read_file(file2)
    #print('lines1:{},lines2:{}',len(lines1),len(lines2))
    #findDiffLines(lines1,lines2)
    #方法体内容
    #dic=findClassBody(file1)
    #print('---类的内容{}'.format(dic[file1]))
    #file_methods_dic=findMethods(dic[file1],file1)
    #start 测试替换
    #row = 'ABC is my favorite ABC , haha, ABC, ABC , See you myABC '
    #old_char = 'ABC'
    #new_char = 'DEFG'
    #str = find_replace_chars(row,old_char,new_char)
    #print(str)
    #end 测试替换
    
    #extremelyFindMethod方法
    #src_file = '/Users/zhangxiao/agilean/valuekanban/python-anti-compile/scripts/examples/dest2/AdminService.java'
    #extremelyFindMethod(src_file)
    '''
    lines = read_file(src_file)
    row_no = 0
    variable = 'admin1'
    tem_variable=getTemVariable(variable)
    print('=>tem_variable:{}'.format(tem_variable))
    for row in lines:
       row_no+=1
       tpl=(row_no,0)
       tpl = get_variable_state (row,row_no,variable,tem_variable,tpl)
       print(tpl)
    '''

    #测试多个功能单元总入口函数

    method_str='public UserDetails loadUserByUsername(Map<Long,String> map, Map<String,Map <Integer, Long> > map2 , Student student) throws UsernameNotFoundException {'
    get_method_param_variables(method_str)
