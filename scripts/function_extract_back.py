# -*- coding: utf-8 -*
import difflib
import sys
import argparse
import os
import re
from method_mark import *
from htmltool import *
#from redistool import *

#result_report=result_folder+'/report/report.txt'
#ratio_file=result_folder+'/report/ratio.txt'
#diff_lines_file=result_folder+'/report/difflines.txt'
#diff_method_file=result_folder+'/report/diffmethods.txt'

#防止递归深度超过最大1000
sys.setrecursionlimit(100000)

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
     
        else: #未尾元素tailTuple[0] 为 } ,与char未配对

           braces.append((char,row,0))
     else:#当前元素左刮号

           braces.append((char,row,0))

     return braces
          

# 读取文件所有的行,去掉所有的注释干扰

def read_file(file_name):
    fopen = open(file_name, 'r')
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
        file_desc = open(file_name, 'r')
        # 读取后按行分割
        text = file_desc.read().splitlines()
        file_desc.close()
        return text
    except IOError as error:
        print(error)
        sys.exit()

 # 比较两个文件并把结果生成一份html文本、相似度、差异行位置
 
def compare_file(file1, file2,result_folder,diff_html_file):
    global global_diff_class_num
    #print ("正在比较文件{0} 和 {1}".format(file1, file2))
    ratios = {}
    differences={}
    if file1 == "" or file2 == "":
        print('文件路径不能为空：第一个文件的路径：{0}, 第二个文件的路径：{1} .'.format(file1, file2))
        sys.exit()
    
    fileName=getFileName(file1)
    #print("fileName:{0}".format(fileName))
    text1_lines = read_file(file1)
    text2_lines = read_file(file2)
    diff = difflib.HtmlDiff()    # 创建HtmlDiff 对象
    content = diff.make_file(text1_lines, text2_lines)  # 通过make_file 方法输出 html 格式的对比结果
    # 将结果写入到result文件中
    result=result_folder+'/'+fileName+'.html'
    try:
        with open(result, 'w') as result_file:
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
    with open(diff_html_file,'a') as diffFile:

      if len(diffs) == 0:

        #diffFile.write('文件:{}与文件{}没有差异行号\n'.format(file1,file2))
        print('文件:{}与文件{}没有差异行号\n'.format(file1,file2))

      else:
        
        global_diff_class_num += 1
        count=0
        size=len(diffs)
        diff_str=''
        for df in  diffs:
            count+=1
            if count == size:
               diff_str+=str(df)
            else:
               diff_str+=str(df)+','
            
            
        differences[file1]=diff_str

      #开始写入html报告
      write_table_td(diffFile,differences)

      

      '''
      ths=['类名','相似度']
      write_table_th(diffFile,'类文件比较相似度',ths)
      write_table_td(diffFile,ratios)
      write_table_tail(diffFile)
      '''
   
def compare_methods(file1,file2,diff_html_file):

   global total_method_number
   global global_diff_method_num
   dic_class_body_1 = findClassBody(file1) # 文件file1方法体,key=file, value=class body

   dic_class_body_2 = findClassBody(file2)

   if dic_class_body_1 is None or dic_class_body_2 is None:
      print('文件:{},没有方法体\n\t'.format(file1))
      return

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
       
   dic_class_body_1={} #清空对象
   dic_class_body_2={}
   
   
   #代码行字典,可以拿到任意两个整数之间的所有行，即函数体内容
   lines1 = read_file(file1) #文件所有的行
   code_dic1=getCodeDic(lines1) #文件所有的行字典，key:行号,value:行内容

   lines2 = read_file(file2) 
   code_dic2=getCodeDic(lines2) #文件所有的行字典，key:行号,value:行内容

   markers1=dic_file_methods_1[file1]
   total_method_number+=len(markers1)
   markers2=dic_file_methods_2[file2]

   diff_funcs={} #函数差异字典

   with open(diff_html_file,'a') as diff_file:
       
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
                   diff_funcs[file1]=marker1.method
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
               dic[getFullFileName(newDir)]=newDir
        else:
            iteratorFolder(newDir,dic)                #如果不是.java文件，递归
    return dic;






    
'''
比较两个folder,生成差异报告
'''
    
def genReport(folder1, folder2, result_folder,diff_html_file):

    global total_class_number
    #先写入htlm报告的头部信息
    with open(diff_html_file,'w') as diffFile:
         wrtie_header(diffFile)
         #先写入类文件比较行改动结果头部
         ths=['类名','行改动位置']
         write_table_th(diffFile,'类文件比较行改动结果',ths)
         
    dic1={}

    dic2={}

    dic1=iteratorFolder(folder1,dic1)

    dic2=iteratorFolder(folder2,dic2)

    #开始写入类文件比较行改动结果,旧与新版本比较
    
   
    
    for k1 in dic1:
      total_class_number+=1
      found=False

      for k2 in dic2:
   
        if k1 == k2 : #同样的文件名进行比较

           found=True
        
           compare_file(dic1[k1],dic2[k2],result_folder,diff_html_file)
           
           break

      
      if found == False:

         #report.write('反编译文件没有找到比较的源码:{0}'.format(k1))
         global_removed_class.append(k1)#从旧版本中移除的类

    #找出新增的文件
    for k2 in dic2:

      found=False

      for k1 in dic1:
   
        if k1 == k2 : #同样的文件名进行比较

           found=True
           break
      if found == False:

           global_added_class.append(k2)#新增的类
           
    #比较完毕写入类文件比较行改动 table tail
    with open(diff_html_file,'a') as diffFile:

          write_table_tail(diffFile)
          ths=['类名','发生变更的函数']
          write_table_th(diffFile,'类文件比较函数变更记录',ths)

        
    #开始写入函数变更记录
    for k1 in dic1:
      
      for k2 in dic2:
   
        if k1 == k2 : #同样的文件名进行比较
        
           compare_methods(dic1[k1],dic2[k2],diff_html_file)
           
           break
    
    #比较完毕，生成函数体变更数据 table tail
    with open(diff_html_file,'a') as diffFile:

          write_table_tail(diffFile)
          

   
    with open(diff_html_file,'a') as diffFile:
         
          #生成新增的函数
          ths=['类名','新增的函数']
          write_table_th(diffFile,'新版本新增函数',ths)
          write_table_td(diffFile,global_added_methods)
          write_table_tail(diffFile)
          #生成移除方法
          ths=['类名','删除的函数']
          write_table_th(diffFile,'新版本删除的函数',ths)
          write_table_td(diffFile,global_removed_methods)
          write_table_tail(diffFile)
          
          #生成新增的类
          ths=['新版本新增的类文件']
          write_table_th(diffFile,'新版本新增的类文件',ths)
          write_table_td(diffFile,global_added_class)
          write_table_tail(diffFile)

          #生成删除的类
          ths=['新版本删除的类文件']
          write_table_th(diffFile,'新版本删除的类文件',ths)
          write_table_td(diffFile,global_removed_class)
          write_table_tail(diffFile)

          #总共的类，更新的类，总共的方法，更新的方法

          ths=['类的总数','更新的类的总数','总共的函数','更新函数']
          write_table_th(diffFile,'类和函数更新情况',ths)
          write_table_td_ele(diffFile,total_class_number,global_diff_class_num,total_method_number,global_diff_method_num)
          write_table_tail(diffFile)
          
          
    #比较完毕，生成html报告的尾部信息 html tail
    with open(diff_html_file,'a') as diffFile:

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

    fopen = open(file, 'r')

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
    
         
#需要考虑:implements,extends情况,获取类的内容{}中间的部分
#新增，提取文件类的内容之前先去掉注释,[\s\S]* <==> .* 不含回车换行
def findClassBody_2(file):

    dic={}

    fopen = open(file, 'r')

    fileread = fopen.read()

    #替换注释部分
    fileread=removeComments(fileread)
    pattern=re.compile(r'\s+public\s+class\s+[A-Za-z0-9_]+\s+(?:implements|extends)*\s[\s\S]*?\{([\s\S.*]*)|\s+public\s+class\s+[A-Za-z0-9_]+\s*\{([\s\S]*)|\s+public\s+abstract\s+class\s+[A-Za-z0-9_]+\s*\{([\s\S]*)')
    
    #print(fileread)
    #pattern=re.compile(r'(?:public)*\s*(?:abstract\s+class|class|interface)+[\s\S]+\{([\s\S]+)')
    #pattern=re.compile(r'\s*public\s+(?:class|interface){1}\s+[A-Za-z0-9_<>,]+\s+(?:implements|extends)*\s+[A-Za-z0-9<>,]+\s*\{([\s\S]*)|\s*public\s+class\s+[A-Za-z0-9_]+\s+\{([\s\S]*)|\s*public\s+abstract\s+class\s+[A-Za-z0-9_]+\s*\{([\s\S]*)')
    #pattern=re.compile(r'\s*public\s+interface\s+[A-Za-z0-9_<>,]+\s*[\s\S<>,]*\{([\s\S<>,]*)|\s*public\s+class\s+[A-Za-z0-9_]+\s*(?:implements|extends)*\s*[\s\S]*\{([\s\S]*)|\s*public\s+class\s+[A-Za-z0-9_]+\s+\{([\s\S]*)|\s*public\s+abstract\s+class\s+[A-Za-z0-9_]+\s*\{([\s\S]*)')
    
    result=pattern.findall(fileread,re.MULTILINE)

    #print('result={}'.format(result))

    for tpls in result:

        
        for tpl in tpls:

            #print('==>tuple:{}'.format(tpl))

            if tpl != '':

               dic[file]=tpl

               return dic
    
    
    #print(result)

    fopen.close()


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

def findMethods_2(dic_class_body,file) :

    #print('==>解析文件:{}'.format(file))

    #使用非贪婪模式匹配 protected,public,private
    result=re.findall(r'(p[a-z]{5,8}\s+.*?{)',dic_class_body.replace('\n',LINE_SHIFT).replace('\t',LINE_SHIFT),re.S)

    #print('==>所有的 method {}'.format(result))

    
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


#标记方法体的起、始行号，方法体内容更可靠

#file: 文件的绝对路径, dic:(key:文件路径,value:MethodMarker[]) 
#函数抽取重要组件
def injectMethodLineNumbers(file,dic):

    methodMarkers=dic[file] #得到一个MethodMarker集合
    lines = read_file(file) #文件所有的行
    numbers=[]
    numberOfMethodMarker=len(methodMarkers)
    #print('==>总共{}个方法'.format(numberOfMethodMarker))
    count_method_marker = 0
    for marker in methodMarkers:#迭代方法标记,找到各个方法的开始行数

       count_method_marker+=1
       #print('==>开始比较第{}个methodMarker method:{},method_str:{}'.format(count_method_marker,marker.method,marker.method_str))

       matched_rows=0;
       for str in marker.method_str.split(LINE_SHIFT):
         row = 0
         for line in lines:
             #print('==>line={},******str={}'.format(line,str))
             row+=1
             if line == '' or line.strip() =='{' or line.strip() == LINE_SHIFT or line.strip().find(';') !=-1 : #空行和单独的{不比较
                continue
             else: #匹配方法的第一行需要考虑全面，容易出错
                if (line.strip().find(str.strip()) !=-1 or str.strip().find(line.strip()) !=-1) and (line.strip().find(marker.method) != -1):
                    #print('==> line.strip():{},str.strip():{}'.format(line.strip(),str.strip()))
                    #print('==>matched at row: {}, str:{}'.format(row,line))
                    marker.start=row
                    numbers.append(row)
                    break #只取命中的第一个子串匹配位置

                    if count_method_marker == numberOfMethodMarker :
                      marker.end=len(lines)
                        
    #print('===>完成方法的起始行定位<=====')    
    #print('===>Total rows:{}'.format(len(lines)))  
    numbers.append(len(lines))

    

    #代码行字典,可以拿到任意两个整数之间的所有行，即函数体内容

    code_dic=getCodeDic(lines)

    
    
    removeNeiborElements(numbers)

    #print('===>移除相差1的元素，保留最少的数作为特征行的行号后元素<=====')
    print('==>方法行：{}'.format(numbers))
    
    if (len(numbers)-1) < numberOfMethodMarker: #不正确

        numberOfMethodMarker=len(numbers)-1
        

    for index in range(0,numberOfMethodMarker): 

      #print('===>index={}'.format(index))
      if (index+1) <= numberOfMethodMarker:
         methodMarkers[index].start=numbers[index]
      
         methodMarkers[index].end=numbers[index+1]-1
      
         
    if (len(numbers)-1) == numberOfMethodMarker:
        cleanMethodMarkers(methodMarkers,code_dic)
    
    #print('====>重置起始行并清洗最后一行后，方法标记对象值<====')
    

    #处理完后，清除不合法的方法标记
    
    methodMarkers=removeInvalidFunc (methodMarkers,code_dic)

    
    
    '''
    for marker in methodMarkers:

      #print('==>start:{},end:{}'.format(marker.start,marker.end))
      
      #str=getCodeByRowNumbers(code_dic,marker.start,marker.end)

      print('==>方法 {}, 函数体:{}'.format(marker.method,marker.body))
    ''' 
    dic[file]=methodMarkers # 更新字典，将新的方法标记对象List作为value

    return dic 


def checkInvalidMethod(method,method_str):

    print('==>method:{},method_str:{}'.format(method,method_str))
    if method.strip().find('==') != -1    or  method.strip().find('RequestMapping') != -1 :
       return  True
    if (not method_str.strip().endswith("{") ) or method_str.strip().endswith(";") :
       return True
    return False

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


def cleanHeaderMethod(methodMarker):

     method = methodMarker.method

     return methodMarker
    
#函数体最后一行清洗
def  cleanMethodMarkers(methodMarkers,code_dic):

    size=len(methodMarkers)
    for index in range(0,size):
        skipLastRow(index,methodMarkers,code_dic)
      
# 函数体最后一行的处理     
def skipLastRow(index,methodMarkers,code_dic):
    try:

      if methodMarkers[index].end <= methodMarkers[index].start:
         return 'pause'
      lastRow=code_dic[methodMarkers[index].end]#最后一行
      if lastRow == '' or (not lastRow.strip().endswith("}") ):

        methodMarkers[index].end=methodMarkers[index].end-1
        skipLastRow(index,methodMarkers,code_dic)#递归
      else:

       return 'ok'
    except KeyError:

       print('Not in Dict--')
       return 'fail'
      
# 移除相差1或者相等的元素，保留最少的数作为特征行的行号
# 核心算法

def removeNeiborElements(numbers) :

    numbers.sort()#asc排序
    removedElements=[]
    size=len(numbers)
    for i in range(0,size):
       j=i+1
       if j <=size-1:
         diff = numbers[j]-numbers[i]
         if diff == 1 or  diff == 0:
            removedElements.append(numbers[j]) 
       else:
         break
    #print('===>输出移除元素<=====')
    for ele in removedElements:

        #print(ele)

        numbers.remove(ele)

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

          continue
        if str.strip().endswith(';') or str.strip().find('||') !=-1 or str.strip().find('&&') !=-1 :

           return True

          

       
    
def  extremelyFindMethod(file):

    
    method_markers=[] #方法标记集合
    #file='/Users/source_code/dian-web/src/main/java/com/hanniu/dian/controller/adm/StaffAdminController.java'
    #file='/Users/source_code/dian-web/src/main/java/com/hanniu/dian/websocket/interceptors/MyHandshakeHandler.java'
    #file='/Users/source_code/dian-web/src/test/java/com/hanniu/online/test/InitDataTestCase.java'
    #file='/Users/source_code/dian-web/src/main/java/com/hanniu/dian/controller/adm/AdminController.java'
   
    #file='/Users/source_code/dian-web/src/main/java/com/hanniu/dian/controller/adm/MerchandiseController.java'
    #file='/Users/zhangxiao/agilean/valuekanban/agilean-rbac-server/src/main/java/cn/agilean/valuekanban/KafkaConsumerConfig.java'
    tpl=findClassBody(file)#返回一个Tuple(lines,dic)

    lines=tpl[0] #避免多次读文件
    dic_class_body=tpl[1]
    body=dic_class_body[file]

    code_dic=getCodeDic(lines) #key:行号,value:行内容,字典
    
    #方法的正则
    #body=body.replace('\t',LINE_SHIFT).replace('\n',LINE_SHIFT)
    #body=removeComments(body)
    
    #body='private void encapsureSortMersMap(List<Merchandise> mers,Map<Long,Sort> sort_map,Map<SortKeyBean,List<Merchandise>> listMap) {'
    #函数括号中的双引号2019/10/24

    if body.strip() == '' :

       return  method_markers
    #2019/10/25 无修饰符的函数: (?:void|[a-zA-Z<>,0-9_.\s]+){1}\s+[a-zA-Z0-9<>,_.@]+\s*\([\s\d\w,<>@\"\(\)=]*\)
    #修复正则：方法返回类型中空格试别不到
    '''
    ConcurrentKafkaListenerContainerFactory<String, KafkaContext> kafkaListenerContainerFactory() {
        ConcurrentKafkaListenerContainerFactory<String, KafkaContext> factory = new ConcurrentKafkaListenerContainerFactory<>();
        factory.setConsumerFactory(kafkaConsumerFactory());
        return factory;
    }
    '''
    #result=re.findall(r'( (?:void|[a-zA-Z0-9<>,_.\s]+){1}\s+[a-zA-Z0-9<>,_.@]+\s*\([\s\d\w,<>@\"\(\)=]*\)\s*[\s\S^;]*?\{|(?:public|private|protected|final){1,2}\s+(?:static|synchronized)?\s*[a-zA-Z<>0-9,.@]*\s*(?:void|[a-zA-Z<>,0-9_.]+){1}\s+[a-zA-Z0-9<>,_.@\s]+\s*\([\s\d\w,<>@\"\(\)=]*\)[\s\S^;]*?\{)',body,re.M)

    #2019/10/24 github
    #/Users/source_code/dian-web/src/main/java/com/hanniu/dian/controller/adm/StaffAdminController.java result=re.findall(r'((?:public|private|protected|final){1,2}\s+(?:static|synchronized)?\s*[a-zA-Z<>0-9,.@]*\s*(?:void|[a-zA-Z<>,0-9_.]+){1}\s+[a-zA-Z0-9<>,_.@]+\s*\([\s\d\w,<>@\"\(\)=]*\)[\s\S^;]*?\{)',body,re.M)
    result=re.findall(r'((?:public|private|protected|final){1,2}\s+(?:static|synchronized)?\s*[a-zA-Z<>0-9,.@]*\s*(?:void|[a-zA-Z<>,0-9_.]+){1}\s+[a-zA-Z0-9<>,_.@]+\s*\([\s\d\w,<>@\"\(\)=]*\)[\s\S^;]*?\{)',body,re.M)
    #today
    #result=re.findall(r'((?:public|private|protected|final){1,2}\s+(?:static|synchronized)?\s*[a-zA-Z<>0-9,.@]*\s*(?:void|[a-zA-Z<>,0-9_.]+){1}\s+[a-zA-Z0-9<>,_.@\s]+\s*\([\s\d\w,<>@\"\(\)=]*\)[\s\S^;]*?\{)',body,re.M)

    
    #print('==>所有的 method {}'.format(result))
    
    dic={} #文件的方法字典,key:文件路径,value: MethodMarker
   

    method_markers=[] #MethodMarker集合
    
    method_str_list=[]
    method_list=[]
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
        #2019/10/23 正确版本
        #res=re.findall(r'([a-zA-Z0-9_.]+\s*\([\s\d\w,<>@\(\)=]*?\))',method_str.strip(),re.M)
        #2019/10/24 正确版本,让方法method正则与完整方法method_str对应
        res=re.findall(r'([a-zA-Z0-9<>,_.@\s]+\s*\([\s\d\w,<>@\"\(\)=]*\))',method_str.strip(),re.M)
       
        #
        if res is not None:

           for method in res:

               #print('==>method:{}'.format(m))

               method_list.append(method)

    #处理一个文件的所有的方法
    size1=len(method_str_list)
    size2=len(method_list)
    #print('******** method size:{}, method_str size:{}*******'.format(size1,size2))
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
           #match_rows=findStartBrace(lines, method_str_list[index],match_rows,code_dic,0)
           
           #match_rows=findMatchRows(method_str_list[index].splitlines(),0,lines,0,match_rows)
           
           match_rows=deepVisit(lines,0,0,method_str_list[index].splitlines(), match_rows)

           
           #print('==>****match_rows:{},method_str size:{}'.format(match_rows,len(method_str_list[index].splitlines())))
           
           if len(match_rows) > 0:
               
               start_row=match_rows[0]
               #根据方法的第一行“花括号”配对方法找最后一行的行号位置
               row_range=getMethodRowRange(code_dic,start_row) #由方法的第一行得到一个Tuple起始行

               tplList.append(row_range)
               
               method_body=getCodeByRowNumbers(code_dic,row_range[0], row_range[1])

    
               method_markers.append(MethodMarker(method_list[index], method_str_list[index], len(method_str_list[index].splitlines()), row_range[0], row_range[1],method_body) )

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
            
        print('==>重叠区域函数处理完毕<=====')

         ##########结束片理重叠区域  ################
        
        '''
        for mmk in method_markers:

           

            print('method_str :{} \n body:{},start:{},end:{}'.format( mmk.method_str,  mmk.body,mmk.start,mmk.end))
        
        '''
        return  method_markers  
          
        
    else: #异常

        print('>>>file:{} 完全方法个数为:{},参数方法个数为:{}'.format(file,size1,size2))

        return  method_markers

    

  
#找出完整方法(存在多行，需要splitlines()按行比较
#lines: 同一个文件的去掉注释和空白行的所有行,method_str:带修饰符、参数、左{ 的完整方法
# match_rows=[] # 找到相等的行集合
#递归查找,方法定位连续行号算法主程
#row:从多少行开始查找,row=0

def findStartBrace(lines, method_str,match_rows,code_dic,row):

    method_str_lines=method_str.splitlines() 
    
    size1=len(method_str_lines)

    size2=len(lines)
    
    #print('==>size:{}'.format(size))
   
    for x in range(0,size1): #方法分成几行
      
      for y in range(row,size2):# 文件行从0到未尾

        row+=1
        #测试用

        if  size1 == 1: #只有一行的方法，找到直接返回
           if lines[y].strip() == method_str_lines[x].strip():
              print('1 Found match at:{},一行方法:{} '.format(row,method_str_lines[x]))
              match_rows.append(row)
              return match_rows
        else:#多行需要递归查找
            
            if lines[y].strip() == method_str_lines[x].strip(): #找到相等行

              #print('2 Found match at:{},一行方法:{} '.format(row,method_str_lines[x]))
              if len(match_rows) >= 1: #如果不是第一行匹配 
                 if row-match_rows[len(match_rows)-1] == 1:#还需要判断是否与前一行行号相差1，需要连续相等
                     
                     match_rows.append(row)
                 else: #不连续相等,说明定位不正确,需要从 match_rows[0] 行重新查找
                     last=match_rows[len(match_rows)-1]
                     match_rows=[] #清空已匹配的行,重置lines从match_rows[len(match_rows)-1]行开始重新查找
                     body=getCodeByRowNumbers(code_dic,last, len(lines))
                     lines=body.splitlines()
                     row=last+1
                     return findStartBrace(lines, method_str,match_rows,code_dic,row)
                     
              else:#第一行匹配，直接加入集合

                    match_rows.append(row)
                    
                    return findStartBrace(lines, method_str,match_rows,code_dic,row)
                    
              break; #查找下一行

         
    return match_rows 
        


#method_str_list: 一个方法的几段字符串 (\n换行)
#lines: 文件的总行数
#返回的行号集合，一个方法在哪连续的几行
#str_star, line_start 首次从0开始
def findMatchRows(method_str_list, str_start,  lines, line_start,rows):

         size1=len(method_str_list)

         size2=len(lines)
    
    
         #比较第x个方法
         if str_start == size1-1 or line_start == size2-1:
             
             return rows
         
         curr_method_str=method_str_list[str_start]

         row_number=0
         for y in range(line_start,size2):
          
         #比较第x个方法
           row_number = y+1  
           if lines[y].strip() == curr_method_str.strip(): #找到相等行    
          
                if size1 <= 1: # 方法只有一行，直接返回
                   rows.append(row_number)
                   return rows
                else: #方法2行以上
                   
                    
                    if len(rows) == 0: # 还没有找到匹配的行号
                       rows.append(row_number) # 加入集合
                       #继续查找
                       
                       curr_method_str=method_str_list[str_start+1]
                       y=0
                       
                    else:#已有匹配的行,方法2个以上
                         
                        #如果当前是行号与rows中未尾的行号不相差1，则清除rows, 从str_start+1位置
                        diff=line_start-rows[len(rows)-1]
                        if diff == 1: #相差1,正常，查找下一个方法遍历
                            rows.append(row_number)
                            str_start+=1#方法下一个
                            line_start+=1#内循环的下一个位置查找 
                            #return findMatchRows(method_str_list, str_start,lines, line_start,rows)
                        else:#相差不为1:

                           rows = []#清空，重新查找
                           str_start=0#重新开始从第一个方法开始查找
                           
                           return findMatchRows(method_str_list, str_start,lines, line_start,rows)
    
         #行数循环结束
         
         return rows

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
旧的和新的比较,有以下结果：
1) 旧的类中的方法在新的类中找不到：删除

2) 旧的类中的方法在新的类中可以找到，但内容不相同： 修改了

3) 新的类中有的方法在旧的类中没有：新增

'''
if __name__ == "__main__":
    #file='/Users/zhangxiao/agilean/valuekanban/git-adapter-server/src/main/java/cn/agilean/gitadapter/service/GitMultiAdapterService.java'
    #file='/Users/zhangxiao/agilean/valuekanban/agilean-rbac-server/src/main/java/cn/agilean/valuekanban/TokenInterceptor.java'
    #file='/Users/source_code/dian-web/src/main/java/com/hanniu/dian/controller/consumer/ConsumerController.java'
    #file='/Users/zhangxiao/agilean/valuekanban/agilean-rbac-server/src/main/java/cn/agilean/valuekanban/KafkaConsumerConfig.java'
    #testFileMethodRowRange(file,18)
   
    #测试移除所有注释函数
    file='/Users/source_code/dian-web/src/main/java/com/hanniu/dian/controller/adm/StaffAdminController.java'
    extremelyFindMethod(file)
    #testRemoveComments(file)
    
    #result_folder='/Users/zhangxiao/agilean/valuekanban/python-anti-compile/dest/result'
    #diff_html_file=result_folder+'/report/report.html'
    
    #folder1='/Users/zhangxiao/agilean/valuekanban/python-anti-compile/dest.back'#反编译
    
    #folder2='/Users/zhangxiao/agilean/valuekanban/python-anti-compile/dest2.back'
    #folder = '/Users/zhangxiao/agilean/valuekanban/python-anti-compile/dest2.back/cn/agilean/valuekanban/repository'
    #redis = getRedis('127.0.0.1',6379,'redis2017',0)
    #extractFunc(folder,redis)
    #print('====>爬虫己完成函数抽取并存入缓存<====')
    #系统参数传入
    '''
    result_folder=sys.argv[1]

    diff_html_file=result_folder+'/report/report.html'

    folder1=sys.argv[2]

    folder2=sys.argv[3]
    '''
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
    '''
    dic=findClassBody(file1)

    print('---类的内容{}'.format(dic[file1]))

    
    file_methods_dic=findMethods(dic[file1],file1)

    injectMethodLineNumbers(file1,file_methods_dic)
    '''
    

