# -*- coding: utf-8 -*-
import difflib
import sys
import argparse
import os
import re
from method_mark import *
from htmltool import *
from batch_decompiler import *
import rewrite_tool as writer
import method_snapshot as snap
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


CHARSET='utf-8'

SUPPORTS='.js,.jsp,.css,.vue'

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
   
         
        
# 花刮号算法主程
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
    fopen = open(file_name, 'r', encoding=CHARSET, errors = 'ignore')
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
        file_desc = open(file_name, 'r',encoding=CHARSET, errors = 'ignore')
        # 读取后按行分割
        text = file_desc.read().splitlines()
        file_desc.close()
        return text
    except IOError as error:
        print(error)
        #sys.exit()


#将当前文件路径除去rootPath的部分

def genFileKey(filePath,rootPath):

    
    return filePath.replace(rootPath,'')

    
    
#获取文件带完整包名的文件名
def getPackageName(file):

    
    filepath, name = os.path.split(file)
    
    file_desc = open(file, 'r',encoding=CHARSET, errors = 'ignore')
   
    lines = file_desc.read().splitlines()
    found = False
    package = ''
    for line in lines:

      if line.strip() == '' or  line.strip().startswith('/') or line.strip().startswith('*'):
         continue
      else:
         #package cn.agilean.gitadapter;
         pattern = re.compile(r'(package\s+[a-zA-Z0-9\.\_]+)')
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

    #print('==>filepath:{},name:{}'.format(filepath,name))
    file_desc = open(file, 'r',encoding=CHARSET, errors = 'ignore')
   
    lines = file_desc.read().splitlines()
    found = False
    package = ''
    for line in lines:

      if line.strip() == '' or  line.strip().startswith('/') or line.strip().startswith('*'):
         continue
      else:
         #print(line+'\n')
         pattern = re.compile(r'(package\s+[a-zA-Z0-9\.\_]+)')
         #m = re.match(r'+(package\s+[a-zA-Z.0-9]+)',line)
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

    return package

#文件预比较
def pre_compare_file(file1, file2):
    
    differences={}
    fileName=getFileName(file1)
    fullFileName = getPackageName(file1)
    text1_lines = read_file(file1)
    text2_lines = read_file(file2)
    #比较差异行的位置
    diffs = findDiffLines(text1_lines, text2_lines)
    return len(diffs) == 0 





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
        with open(result, 'w',encoding=CHARSET, errors = 'ignore') as result_file:
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
    with open(diff_html_file,'a',encoding=CHARSET, errors = 'ignore') as diffFile:

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

    #print('==>filepath:{}'.format(filepath))
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

   with open(diff_html_file,'a',encoding=CHARSET, errors = 'ignore') as diff_file:
       
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

 将所有的filepath下面的文件都写入字典
 
'''

def iteratorFolder(filepath,dic):
    
    fileNames = os.listdir(filepath)  # 获取当前路径下的文件名，返回List
    for file in fileNames:
        newDir = filepath + '/' + file
        
        # if os.path.isdir(newDir): # 如果是文件夹
        if os.path.isfile(newDir):  # 如果是文件
            #print(newDir)
            #print(os.path.splitext(newDir)[1])
            suff=os.path.splitext(newDir)[1]
            
            if suff == ".java":  # 判断是否是.java
            
               #dic[getFullFileName(newDir)]=newDir
               dic[getPackageName(newDir)] = newDir # 使用包名+文件名避免重名文件
            else: # 支持比较的文件
                if suff:
                  if SUPPORTS.find(suff) != -1:
                    #print('==>support:{}'.format(newDir))
                    fileKey = genFileKey(newDir,filepath)
                    print('=>fileKey:{}'.format(fileKey))
                        
                    dic[fileKey] = newDir
                  else:
                    pass
        else:
            
            iteratorFolder(newDir,dic)                #如果不是.java文件，递归
    return dic;



def init_variables():


    global_removed_methods={}#相对于旧的版本移除的方法(旧的类中有的方法，新的类中没有), k=文件路径，value:[]
    global_added_methods={}  #新的类中有的方法旧的类中没有 
    global_added_class=[] # 旧版本中缺少的文件,新增文件
    global_removed_class=[]#旧版本中有的文件，新版本中删除
    global_diff_class_num = 0
    global_diff_method_num = 0
    total_method_number=0
    total_class_number=0   #总共的类
    total_master_class_num=0 #master分支JAVA文件总数


# 新的报告流程
# 2019/01/17 需要新增其他非JAVA文本文件的比较,HTML报告注明哪边是MASTER哪边是生产
def genReport(folder1, folder2, result_folder,diff_html_file):

    global total_class_number

    total_class_number = 0
    global total_master_class_num

    total_master_class_num = 0


    #初始化变量，避免用户不关闭界面直接运行
    init_variables()

    #noisy_file_dic1 = {} #key:文件路径，value: True,旧版本
    #noisy_file_dic2 = {} #key:文件路径，value: True,新版本
    print('==>生产版本文件夹：{}'.format(folder1))
    print('==>master版本文件夹：{}'.format(folder2))
    if not os.path.exists(result_folder):

      os.makedirs(result_folder)
            
    parent_path = os.path.dirname(diff_html_file)

    if not os.path.exists(parent_path):

      os.makedirs(parent_path)
    
    if not os.path.exists(diff_html_file):
           file = open(diff_html_file, 'w', encoding=CHARSET, errors = 'ignore')
           
           file.close()
    
    print('******step1,备份反编译后的源文件*****')
    
    
    print('******step2,先写入html报告的头部信息*****')
    with open(diff_html_file,'w',encoding=CHARSET, errors = 'ignore') as diffFile:
         wrtie_header(diffFile)
         #先写生产文件比较行改动结果头部
         ths=['文件名','行改动位置']
         write_table_th(diffFile,'生产版本文件比较行改动结果',ths)
         
    dic1={}
    dic2={}
    dic1=iteratorFolder(folder1,dic1)
    dic2=iteratorFolder(folder2,dic2)
    print('******step3,找出有差异的文件字典************')

    size1 = len(dic1)
    size2 = len(dic2)

    
    
    different_dic = {}# 有差异的文件字典
   
    for k1 in dic1:
      for k2 in dic2:
        if k1 == k2 : #同样的文件名进行比较
           #有差异行
           if not pre_compare_file(dic1[k1],dic2[k2]): #预比较不用写报告内容，仅仅比较行内容
                different_dic[k1] = dic1[k1] 
           break
              
    print('==>消除噪音之前,总共:{}个文件差异'.format(len(different_dic)))

    #降噪之前差异文件个数 
    diff_count_before = len(different_dic)
    
    print('******step4,所有的java方法降噪处理***********')
    
    for k1 in different_dic:

        for k2 in dic2:

            if k1 == k2: #文件名相同比较
               file1 = different_dic[k1]
               file2 = dic2[k2]
               if file1.endswith('.java'):
                 lines1 = read_file(file1) #文件所有的行,去掉注释后的行
                 lines2 = read_file(file2) #文件所有的行,去掉注释后的行
                 #完成多余this替换,更新文件内容
                 writer.replaceThis(lines1,file1)
                 writer.replaceThis(lines2,file2)
                 #完成降噪处理，更新文件内容
                 writer.eleminate_noisy(file1,file2)
        
               break
    
    new_different_dic = {}#降噪后，有变化字典
    #降噪后再查找一下新的差异文件清单
    print('******step5,降噪后再次比较文件差异***********')
    count = 0
    for k1 in different_dic: #仅在有差异的类中进行
      count+=1
     
      for k2 in dic2:
   
        if k1 == k2 : #同样的文件名进行比较

           if count % 80 == 0:
              print('******降噪后比较:{}/{}*******'.format(count,size1))
           #没有差异行
           if not pre_compare_file(different_dic[k1],dic2[k2]): 
                new_different_dic[k1] = different_dic[k1]
               
           break
       

    different_dic = {}
   
    diff_count_after = len(new_different_dic)
    diff_last = diff_count_before - diff_count_after
    print('******降噪前文件差异数：{}，降噪后文件差异数:{},减少噪音文件数:{}'.format(diff_count_before,diff_count_after,diff_last))
    print('******step6,降噪完成，开始生成差异报告***********')

    #降噪后写文件差异报告 
    count = 0
    for k1 in new_different_dic: #仅在有差异的类中进行
      count+=1
      for k2 in dic2:
        if k1 == k2 : #同样的文件名进行比较
           if count/80 == 0: # 80整数才输出
             print('******正在写文件行差异:{}/{}*******'.format(count,size1))
           
           compare_file(new_different_dic[k1],dic2[k2],result_folder,diff_html_file)
               
           break


    #生产版本中有的，master版本中没有
    found = True
    for k1 in dic1:
       total_class_number+=1
       for k2 in dic2:
           found = False
           if k1 == k2:
              found = True
              break
           
       if not found:

           global_removed_class.append(k1)#生产版本中有的，master版本中没有的文件
               
               

    
    #找出新增的文件
    for k2 in dic2:
      total_master_class_num+=1
      found=False

      for k1 in dic1:
   
        if k1 == k2 : #同样的文件名进行比较

           found=True
           break
      if found == False:

           global_added_class.append(k2)#,生产版本中没有的，master的版本中有，master版本中新增的类
           
    #比较完毕写入类文件比较行改动 table tail
    with open(diff_html_file,'a',encoding=CHARSET, errors = 'ignore') as diffFile:

          write_table_tail(diffFile)
          ths=['java文件名','发生变更的函数']
          write_table_th(diffFile,'生产java文件比较函数变更记录',ths)

        
    #开始写入函数变更记录
    count = 0
    total = len(dic1) #旧版本总共文件数 
    dic1 = {}
    for k1 in new_different_dic: #在降噪后的差异行中比较
      count+=1

      if count/80 == 0: # 80整数才输出
          print('******写入函数变更记录{}/{}*******'.format(count,total))
      
      for k2 in dic2:
        
        if k1 == k2 : #同样的文件名进行比较
        
            compare_methods(new_different_dic[k1],dic2[k2],diff_html_file)
            break
   
    print('******写入函数变更记录写入完毕********')

    print('******step7, 开始写入汇总信息********')
    dic2={}
    new_different_dic={}
    #比较完毕，生成函数体变更数据 table tail
    with open(diff_html_file,'a',encoding=CHARSET, errors = 'ignore') as diffFile:

          write_table_tail(diffFile)
          

   
    with open(diff_html_file,'a',encoding=CHARSET, errors = 'ignore') as diffFile:
         
          #生成新增的函数
          ths=['java文件','master版本有，生产版本没有的的函数统计']
          write_table_th(diffFile,'master版本新增函数',ths)
          write_table_td(diffFile,global_added_methods)
          write_table_tail(diffFile)
          #生成移除方法
          ths=['java文件','master版本没有，生产版本有的的函数统计']
          write_table_th(diffFile,'master版本删除的函数',ths)
          write_table_td(diffFile,global_removed_methods)
          write_table_tail(diffFile)
          
          #生成新增的类
          ths=['在master版本有的文件，在生产版本没有的文件统计']
          write_table_th(diffFile,'master版本新增的文件',ths)
          write_table_td(diffFile,global_added_class)
          write_table_tail(diffFile)

          #生成删除的类
          ths=['master版本没有，生产版本有的文件统计']
          write_table_th(diffFile,'master版本删除的文件',ths)
          write_table_td(diffFile,global_removed_class)
          write_table_tail(diffFile)

          #总共的类，更新的类，总共的方法，更新的方法

          ths=['生产版本文件的总数','master版本文件总数','master版本同生产版本相比，发生更新的文件总数','master版本同生产版本相比,发生变动行的java文件中总共的函数数量','master版本同生产版本相比,发生更新函数',]
          write_table_th(diffFile,'文件和函数更新',ths)
          write_table_td_ele(diffFile,total_master_class_num,total_class_number,global_diff_class_num,total_method_number,global_diff_method_num)
          write_table_tail(diffFile)

          #降噪效果
          ths=['降噪前差异文件数','降噪后差异文件数','降噪后减少文件差异数']
          write_table_th(diffFile,'降噪效果',ths)

          col=[str(diff_count_before),str(diff_count_after),str(diff_last)]
          write_table_td_row(diffFile,col)
          write_table_tail(diffFile)
          
          
    #比较完毕，生成html报告的尾部信息 html tail
    with open(diff_html_file,'a',encoding=CHARSET, errors = 'ignore') as diffFile:

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
            str = str.replace('\r','').replace('\n','').replace('\t','')
            body=body+str+'\n'
    #去掉\t标识
    
    return body



#测试移除注释部分
def testRemoveComments(file):

    fopen = open(file, 'r',encoding=CHARSET, errors = 'ignore')

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
    '''
    for method_str in result:

       print(method_str)
    '''
#无修饰符函数正则 
def testNonModifierFunc(file):
    tpl=findClassBody(file)#返回一个Tuple(lines,dic)
    lines=tpl[0] #避免多次读文件
    dic_class_body=tpl[1]
    body=dic_class_body[file]
    result=re.findall(r'((?:^public^private[A-Z]){1}[a-zA-Z0-9<>,_]{1,}\s*\([\s\d\w,<>@\"\(\)=]*\)[\s\S^;]*?\{)',body,re.S)

    print(result)

#2019/12/20 重写了方法搜索整体逻辑，整体更简洁、更可靠
def  extremelyFindMethod(file):

   return snap.find_all_methods(file)

#新增方法体变量搜集 
def  extremelyFindMethod_old(file):

    
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
    #2019/12/17
    #result=re.findall(r'((?:public|private|protected|final){1,2}\s+(?:static|synchronized)?\s*[a-zA-Z<>0-9,.@]*\s*(?:void|[a-zA-Z<>,0-9_.]+){1}\s+[a-zA-Z0-9<>,_.@]+\s*\([\[\]\s\d\w,<>@\"\(\)=]*\)[\s\S^;]*?\{)',body,re.M)
    #Array , eg: private int[] cal() { 
    result=re.findall(r'((?:public|private|protected|final){1,2}\s+(?:static|synchronized)?\s*[\[\]a-zA-Z<>0-9,.@]*\s*(?:void|[\[\]a-zA-Z<>,0-9_.]+){1}\s+[\[\]a-zA-Z0-9<>,_.@]+\s*\([\[\]\s\d\w,<>@\"\(\)=]*\)[\s\S^;]*?\{)',body,re.M)
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

        res=re.findall(r'([a-zA-Z0-9._]+\s*\([\[\]\s\d\w,<>@\"\(\)=]*\))',method_str.strip(),re.M)
        
        if res is not None:

           for method in res:

               #print('==>method:{}'.format(method))
               if method_str.strip().find(method.strip()) != -1: #只取一个正确的方法
                   method_list.append(method)
                   break
               
               

    #处理一个文件的所有的方法
    size1=len(method_str_list)
    size2=len(method_list)
    #print('==>file:{},method size:{}, method_str size:{}<=='.format(file,size1,size2))
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

                #print('==>删除重叠区域函数：{} '.format(olpMK.method))

                method_markers.remove(olpMK)
            
        #print('==>重叠区域函数处理完毕<=====')

         ##########结束片理重叠区域  ################
        
        #print('===>找到函数:{}个,清单:\n'.format(len(method_markers)))
        
    
        size = len(method_markers) 
        for index in range(0,size): #遍历方法集合

           mmk = method_markers[index]

           #method_body: 方法体中找出variables
           col = findVariables(mmk)

           #print('=>method_str:{},variables:{}'.format(mmk.method_str,col))
           
           #print('=>set:{}'.format(set))
           #获取方法的参数字符串
           param = get_method_param(mmk.method_str)
           params = get_method_param_variables (mmk.method_str)

           #print('=>method_str:{},params:{}'.format(mmk.method_str,params))
        
           #为避免同名不同参函数混淆，需要将参数处理成对象集合
           if  len(params) > 0 :
               
               variable_collection = reset_method_param_variables(params)
               
               method_no_param = mmk.method_str.replace(param,str(variable_collection))
               
           else:
               
               method_no_param = mmk.method_str
               
           method_markers[index]= MethodMarker(mmk.method, mmk.method_str, mmk.method_str_rows, mmk.start, mmk.end,mmk.body,col,params,method_no_param) 


        #遍历方法标记集合
        '''
        for mmk in method_markers:
            print('start:{},end:{},method_str:{},method_no_param:{},variables:{},params:{}'.format(mmk.start,mmk.end,mmk.method_str,mmk.method_no_param,mmk.variables,mmk.params))
        '''
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

还需要定位set中的变量出现的行位置、以参数|调用|赋值形式出现 [('变量名1','变量类型','final|empty',[(第几行,出现次数,...]),...]

每个方法的内部变量集合(排序)

example: variables:
variables:[('date', 'Date', '', [(3, 1)],1), ('flag', 'String', '', [(4, 1), (6, 1), (8, 1)],2), ('time', 'String', '', [(2, 1)],3), ('timeout', 'String', '', [(5, 1), (7, 1)],4)]
'''

def findVariables (method_marker):

 body = method_marker.body
 hashset = set()

 sequence = 0
 #print('==>body:{},起始行：{}'.format(method_body,start))
 #先找出所有的函数体内的变量，从赋值语句中查找,变量在方法体中的第几行中出现了多少次置为空集合[], 在 get_variable_state 方法中填充集合值

 lines = body.splitlines()
 for row in lines:
     
     #在用逗号分割之前先清理空格
     row = row.replace(' ;',';').replace('; ',';').replace(' ,',',').replace(', ',',').replace(' <','<').replace('< ','<').replace(' =','=').replace('= ','=').replace(' [','[').strip()

     #step1: for循环中的变量
     pattern = re.compile(r'for\((.*)\)')

     match = pattern.search(row)

     try:
        if match:

           res = match.group(1) # int i = 0; i<10; i++  OR  Map entry: hashMap

           get = False
           if res.find(':') != -1:
           
              left_parts = res.split(':')[0].split(' ')
              get = True

              
           elif res.find(';') != -1:

              left = res.split(';')[0]

              left_parts = left.split('=')[0].split(' ')
              get = True
           if get:
             size = len(left_parts)
             if size == 4:
                if validateVariable(left_parts[3]):
                   sequence+=1
                   hashset.add( (left_parts[3],left_parts[2],left_parts[0]+' '+left_parts[1],None,sequence) )
                    
             elif size == 3: #变量带有修饰
                if validateVariable(left_parts[2]):
                   sequence+=1
                   hashset.add( (left_parts[2],left_parts[1],left_parts[0],None,sequence) )

             elif size == 2: #无修饰符

                if validateVariable(left_parts[1]):
                   sequence+=1
                   hashset.add( (left_parts[1],left_parts[0],'',None,sequence) )
               

     except Exception as e:

         pass
     #end of for 循环中的变量
        
     #step2: catch(Exception e) 变量捕获
     pattern = re.compile(r'catch\s*\((.*)\)')

     match = pattern.search(row)
     try:
       if match:
          left_parts = match.group(1).strip().split(' ')
          #print('***left_parts:{}'.format(left_parts))
          size = len(left_parts)
          if size == 4:
                 if validateVariable(left_parts[3]):
                   sequence+=1
                   hashset.add( (left_parts[3],left_parts[2],left_parts[0]+' '+left_parts[1],None,sequence) )
                    
          elif size == 3: #变量带有修饰
                if validateVariable(left_parts[2]):
                   sequence+=1
                   hashset.add( (left_parts[2],left_parts[1],left_parts[0],None,sequence) )

          elif size == 2: #无修饰符

                if validateVariable(left_parts[1]):
                   sequence+=1
                   hashset.add( (left_parts[1],left_parts[0],'',None,sequence) )
          
     except Exception as e:
         
         pass

     

        
     if row.find('!=') != -1 or row.find('==') != -1 or row.find('>=') != -1 or row.find('<=') != -1: #含有=符号的判断语句，不考虑变量赋值语句 

         #需要考虑三方运算 express =  express1 ? XXX : yyy
         if row.find('?') != -1 and row.find(':') != -1:

             eq_index = row.find('=')

             left_parts = row[eq_index:]


             size = len(left_parts)
             if size == 4:
                 if validateVariable(left_parts[3]):
                   sequence+=1
                   hashset.add( (left_parts[3],left_parts[2],left_parts[0]+' '+left_parts[1],None,sequence) )
                    
             elif size == 3: #变量带有修饰
                if validateVariable(left_parts[2]):
                   sequence+=1
                   hashset.add( (left_parts[2],left_parts[1],left_parts[0],None,sequence) )

             elif size == 2: #无修饰符

                if validateVariable(left_parts[1]):
                   sequence+=1
                   hashset.add( (left_parts[1],left_parts[0],'',None,sequence) )
          
             

         else: # 其他情况暂不考虑

          pass

     # 以 = 隔开的定义变量
     words = row.split('=');
     
     if len(words) > 1: # 只处理 = 表达式的情况 

        left_part = words[0].strip() # = 表达式的左边定义变量部分

        #print('==>left_part:{}'.format(left_part))
        
        left_parts = left_part.split(' ')

        size = len(left_parts) # 需要两个以上的分词才具有变量类型，才是变量赋值语句

        #print('==>2,size'.format(size))

        if size > 1:
            
           
  
                #if validateVariable(left_parts):

                #print('=>valid:{},size:{}'.format(left_parts,size))

                if size == 4:
                    if validateVariable(left_parts[3]):
                       sequence+=1
                       hashset.add( (left_parts[3],left_parts[2],left_parts[0]+' '+left_parts[1],None,sequence) )
                    
                elif size == 3: #变量带有修饰
                    if validateVariable(left_parts[2]):
                       sequence+=1
                       hashset.add( (left_parts[2],left_parts[1],left_parts[0],None,sequence) )

                elif size == 2: #无修饰符
                    if validateVariable(left_parts[1]):
                       sequence+=1
                       hashset.add( (left_parts[1],left_parts[0],'',None,sequence) )
     
     #处理空赋值的场景                
     elif len(words) == 1: # int a;

          if row.endswith(';'): #赋空值语句

              row = row.replace(';','')

              if row == ' ':
                 pass
              else:
                 left_parts = row.strip().split(' ')
       
                 size = len(left_parts)

                 if size == 1:
                     pass
                 else:

                      if size == 4:
                          if validateVariable(left_parts[3]):
                             sequence+=1
                             hashset.add( (left_parts[3],left_parts[2],left_parts[0]+' '+left_parts[1],None,sequence) )
                    
                      elif size == 3: #变量带有修饰
                          if validateVariable(left_parts[2]):
                             sequence+=1
                             hashset.add( (left_parts[2],left_parts[1],left_parts[0],None,sequence) )

                      elif size == 2: #无修饰符
                          if validateVariable(left_parts[1]):
                             sequence+=1
                             hashset.add( (left_parts[1],left_parts[0],'',None,sequence) )

                         
                     

 #转set为list

 collection = list(hashset)


 size =  len(collection)

 if size == 0: #方法没有定义内部变量

    return []

 col = []

 for  tp in collection:

       col.append((tp[0],tp[1],tp[2],[],tp[4]))
       
 collection = []
 
 

 # 再次遍历，找到变量所在的位置和形态(参数传入，调用方法，赋值,需要判断
 row_no = 0 #统计方法的行数
 for row in body.splitlines():

     row_no+=1

     for index in range(0,size):

          tpl = col[index] # (变量名、类型、修饰符,[(方法第N行，出现次数,...], 定义变量的次序)

          variable = tpl[0] #变量名
          tem_variable = getTemVariable(variable)
          tem_tpl = (row_no,0)
          #得到变量在一行中出现了多少次
          variable_position_tpl = get_variable_state (row,row_no,variable,tem_variable,tem_tpl)

          if variable_position_tpl[1] > 0: #说明变量在该行至少出现了1次

              tpl[3].append(variable_position_tpl)
           
 #依据变量出现的顺序来排序
 col.sort(key=lambda tpl: tpl[4])
 return col

 


CAL_LEFT= '()+-*/%><=,;[].!{}:'
CAL_RIGHT ='()+-*/%><=,;.][!{}:'

#row_no: 方法的第几行
#找出一个变量在行中出现的次数,如： (3,1):在第3行中出现了1次
#tem_variable:临时替换变量
def get_variable_state (row,row_no,variable,tem_variable,tpl):

    
        index  =  row.find(variable) 
        size = len(variable)

        if index == -1:
           return tpl
        

        valid = validate_standalone_variable(row,index,size)
        
        row = '{}{}{}'.format(row[0:index],tem_variable,row[(index+size):])
        
        #print('row:{},valid:{}'.format(row,valid))
        if valid:
            #[(第几行,出现次数),...]
            tpl = (tpl[0],tpl[1]+1)
        
            #print('=>replace row:{}'.format(row))
            return get_variable_state(row,row_no,variable, tem_variable,tpl)
        else:#不合法接着找
            return get_variable_state(row,row_no,variable, tem_variable,tpl)

#判断一个变量在行中出现的位置是否合法，作为公共的函数
#row:具体的行,index:出现的索引位置,size: 变量长度
def validate_standalone_variable(row,index,size):

        left = row[(index-1):index].strip()
     
        right = row[(index+size):(index+size+1)].strip()

        #判断是否以一个单独的单词出现
        valid = True
        #左右均不为空
        if  left != ' '   and right != ' ':

           if CAL_LEFT.find(left) != -1 and CAL_RIGHT.find(right) != -1: 
               pass
           else:
               valid = False
        #左右均为空
        elif left == ' ' and  right == ' ':
            pass
        #左不为空，右为空
        elif left != ' ' and right == ' ':
            if CAL_LEFT.find(left) != -1:
               pass
            else:
                valid = False
        elif left == ' ' and  right != ' ':
            if CAL_RIGHT.find(right) != -1:
               pass
            else:
                valid = False
        else:
            pass
    
        return valid

    
#得到与变量一样长度的临时变量^^^
def getTemVariable(variable):

   size = len(variable)
   str=''
   for i in range(0,size):
    str+='^'
   return str 
       
        
#校验变量是否为合法java变量
def validateVariable(variable):

    pattern = re.compile(r'([a-zA-Z0-9_]+)')
    
    match = pattern.search(variable)
     
    if match:

      if match.group(1) == variable:

          return True
      
    return False
        

def get_method_param(method_str):

    str = ' '
    #method_str='public UserDetails loadUserByUsername(Map<Long,String> map, Map<String,Map<Integer) throws UsernameNotFoundException {'
    
    pattern = re.compile(r'\(([\s\d\w,<>@\"\(\)=\[\]]*)\)')

    match = pattern.search(method_str)

    if match:

      #print(match.group(1))
      str = match.group(1)
      
    return str   


#清洗表达式的唯一入口
def clean_str(str):

    if  str == ' ' or len(str.strip()) == 0:
        return str
    return str.replace(' ;',';').replace('; ',';').replace(' ,',',').replace(', ',',').replace(' <','<').replace('< ','<').replace(' =','=').replace('= ','=').replace(' [','[').strip()

    

#获取一个方法method_str的所有的形参，处理成  ('变量名1','变量类型',[(第几行,出现次数),...],'empty|final')

'''
method_no_param:public void addAdmin(['Admin', 'Select'])  throws Exception{,

#变量及出现的行号、次数
variables:[('m', 'Merchandise', '', [(17, 1), (18, 1), (19, 1), (20, 1), (21, 1)]),
           ('merchandises', 'List<Merchandise>', '', [(15, 1), (16, 1), (17, 1), (23, 1)]),
          ('newShop', 'Shop', '', [(6, 1), (11, 1), (20, 1), (28, 1), (30, 1)]),
          ('sdf', 'SimpleDateFormat', '', [(2, 1), (4, 1), (19, 1)]),
          ('shop', 'Shop', '', [(3, 1), (4, 1), (5, 1), (6, 1)]),
          ('sortIds', 'List<Long>', '', [(9, 1), (12, 1), (21, 1)]),
          ('sorts', 'List<Sort>', '', [(8, 1), (10, 1)]),
          ('terminals', 'List<Terminal>', '', [(26, 1), (27, 1), (36, 1)])],
#方法的参数Tuple集合
params:[('admin', 'Admin', 'final'), ('select', 'Select', '')]

'''

def get_method_param_variables(method_str):

    
    #依据正则提取方法参数字符串
    st= get_method_param(method_str)
    #st = st.replace(' ;',';').replace('; ',';').replace(' ,',',').replace(', ',',').replace(' <','<').replace('< ','<').replace(' =','=').replace('= ','=').replace(' [','[').strip()
    st = clean_str(st)
    

    if st == ' ': # 说明没有参数
        return [] 
    commas = find_valid_commas(st) #[20,60]
    #print('==>method_str:{},commas:{}'.format(method_str,commas))
    variables = find_valid_param_variables(st,commas)
    #print('==>method_str:{},param variables:{}'.format(method_str,variables))
    return variables
    
#参数字符串param,由get_method_param(method_str)获取,取方法中的参数类型，不取变量名称

def reset_method_param_variables(params):

    #print(params)
    collection = []
    if not params:
       return collection
    if len(params) == 0:

       return collection
    
    for tpl in params:

        collection.append(tpl[1])

    return collection
    

# 找出< 和 > 符号集合，再组装成元组 [ (<,>) ,(<,>) ... ]

# JDK泛型、注解类的参数也支持
'''
springMVC中类似以下方法：
springSecurityCheck(@RequestParam(value="username",required=true) final String username,
			                                @RequestParam(value="password",required=true) final String password)


char1: <

char2: >
'''		                                     
def find_angle_barces(str,char1,char2):

    c1 = find_char_position(str,char1,[]) #泛型 < 的边界

    c2 = find_char_position(str,char2,[]) #泛型 > 的边界

    size = len(c1)

    collection = [] 
    for i in range(0,size):

        collection.append( ( c1[i], c2[i] ))
    
    return collection
    
# 方法参数字符串中有效的字符串集合索引位置,先处理<>型中的逗号

def find_valid_commas(str):

   #print('=>获取方法参数字符串:{}'.format(str))
   commas = find_char_position (str,',',[]) # 参数字符串中多少个逗号

   #print('==>before:逗号：{}'.format(commas))

   size = len(commas)

   removed_commas = [] 

   if str.find('<') == -1 and str.find('(') == -1 :# 没有泛型符号和注解()符号

      #print('==>没有泛型符号<==, 索引位置:{}'.format(commas))

      return commas
      
   if str.find('<') != -1: # 有泛型符号
    
     angles =   find_angle_barces (str,'<','>') # 得到一个 (<,>) 元组集合
     #print('==>泛型:<>索引:{}'.format(angles  ))
     if len(angles) > 0:

         for i in range(0,size):

          comma = commas[i]

          for angle in angles:
              if comma > angle[0] and comma < angle[1]:
                 removed_commas.append(comma)
                 break

   if str.find('(') != -1: # 有注解符号()
    
      angles =   find_angle_barces (str,'(',')') # 得到一个 ((,)) 元组集合

      #print('==>注解:逗号：{}'.format(angles  ))

      if len(angles) >0:
        for i in range(0,size):

          comma = commas[i]

          for angle in angles:
              if comma > angle[0] and comma < angle[1]:
                 removed_commas.append(comma)
                 break
   
   #删除无用逗号索引
   if len(removed_commas) > 0:
        for cm in  removed_commas:

          commas.remove(cm)
      #print('==>处理完后:逗号：{}'.format(commas))
   return commas;
# 从方法参数字符串str中，根据有效的逗号索引位置，组装参数变量元组集合[('变量名', '变量类型', '修饰符'),...] 
def find_valid_param_variables ( str, commas):
   
   variables = []
   if  commas is None:
       return variables
   size = len(commas)

   #print('commas size:{},commas:{}'.format(size,commas))

   #if size == 0: #没有逗号
   #    return variables
   
   if size == 0:# 只有一个参数

       comma = assembly_variable_tuple(str)
       if comma is not None:
          variables.append(comma)
       
   elif size > 0:
       
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

           if param is not None:
             #print('==>param:{}'.format(param))
             variables.append(param)
           
       
   return  variables   
      
# 除掉空白的元素
def remove_space(array):

    size = len(array)
    removed_array = [] 
    if len(array) <= 1:

        return array 
    for i in range(0,size):

        ele = array[i]

        if len(ele) == 0: #长度为0的元素，直接移除
            removed_array.append(ele)

    if len(removed_array) > 0:

       for ele in removed_array:
           array.remove(ele)
           
    return array

# param 一个表达式 eg: final String abc
# 泛型变量空格需要处理  ('变量名', '变量类型', '修饰符')
# 由一个参数表达式获取变量Tuple唯一入口 
def assembly_variable_tuple (param):

    param = clean_str(param)
     
    array  = param.split(' ')
    array = remove_space(array)
    if len(array) == 2:

        return (array[1],array[0],'')

    elif len(array) == 3:
       return (array[2],array[1],array[0])
    elif len(array) == 4:
      return (array[3],array[2],array[0]+' '+array[1])

    #@PathVariable (required=false)  String tableNo
    else: 
      #print('=== warning: param {}参数错误'.format(param))
      return None
    
#将反编译的文件读取，写入目标文件
#src_file: 反编译文件
#dest_file: 去掉注释、空行之后的行所入到dest_file文件
def write_tidy_file(src_file,dest_file):

    datas = read_file(src_file) #文件所有的行,去掉注释后的行
    
    fo = open(dest_file, 'w', encoding=CHARSET, errors = 'ignore')

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
#*******************start 按行替换变量主程*********************
#替换合法的变量old_char为新变量new_char,tem_char是临时变量，先所有的都替换(含合法、非合法变量),不合法用临时变量替换，最后将临时变量替换成非合法变量
#采用 index查找，可以从指定的起始行查找，跳过不合法变量进行查找

def replace_valid_varaibles(row,variable,new_variable,start):

     size = len(variable)

     size2 = len(new_variable)

     diff = size2-size #可以是一个负数
     try:

       
       index = row.index(variable,start) #从start位置开始查找,首次为0

       valid = validate_standalone_variable(row,index,size)
       
       if valid: #合法的变量，直接用新变量替换
            
            if validate_variable_fallin_quoatations(index,row,'"'):
               #print('变量:{}落在双引号表达式中，忽略替换'.format(variable))
               #重新查找另外一个变量位置
               return  replace_valid_varaibles(row,variable,new_variable,index+size)
            
            row = '{}{}{}'.format(row[0:index],new_variable,row[(index+size):])
            
            return  replace_valid_varaibles(row,variable,new_variable,index+size+diff)   
       else:
           return  replace_valid_varaibles(row,variable,new_variable,index+size)   
 
     except Exception as e: #找不到直接抛异常
       #print('=Not found<=')

       return row
    
#*******************end 按行替换变量主程*********************
#查看变量索引有没有落在双引号的期间
#index:变量在row字符串中出现的索引
#char: 双引号, 为True 说明变量落在了双引号期间
def validate_variable_fallin_quoatations(index,row,char):
    
    variables  = find_quoatations(row,char)

    if len(variables) == 0: #没有双引号,变量的索引未落在双引号的区间

        return False
    
    found = False
    for tpl in variables:

        if index > tpl[0] and index < tpl[1]:

            found = True
            break
    
    return found    



#返回一个行中所有的双引号的集合坐标 [ (x1,y1,(x2,y2) ...], char ='"'
def find_quoatations(row,char):

   variables = []
   commas = [] 
   commas = find_char_position(row,char,commas)
   
   if  commas is None:
       return variables
   size = len(commas)

   if size == 0:# 没有char符号

      return variables
       
   elif size > 0:

       if (size % 2) != 0:

         return variables
        
       for i in range(0,size-1,2):

           for j in range (i+1,size):
               
                variables.append( (commas[i],commas[j]))
                break
              
   return  variables   

        


    
#查找一个char出现在字符串中索引的位置，放在集合中
# eg: str = 'Map<Long,String> map, Map<String,String> map2'
def find_char_position (str,char,collection):

    
    index  =  str.find(char)
    
    size = len(char)
    #得到与char一样长的临时变量
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
    '''
    folder1 = '/Users/zhangxiao/agilean/valuekanban/python-anti-compile/scripts/examples/dest1'
    folder2 = '/Users/zhangxiao/agilean/valuekanban/python-anti-compile/scripts/examples/dest2'
    result_folder = '/Users/zhangxiao/agilean/valuekanban/python-anti-compile/scripts/examples/report'
    diff_html_file='/Users/zhangxiao/agilean/valuekanban/python-anti-compile/scripts/examples/report/report.html'
    genReport(folder1,folder2,result_folder,diff_html_file)
    '''

    
    
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

    #测试get_variable_state (row,row_no,variable,tem_variable,tpl)
    '''
    row = 'boolean accountNonExpired = true;'
    row_no = 20

    variable = 'accountNonExpired'

    tem_variable = '^^^^^^^^^^^^^^^^^'

    tpl = (20, 0)

    tpl = get_variable_state (row,row_no,variable,tem_variable,tpl)

    print(tpl)
    '''
    
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

    #method_str='public ModelAndView springSecurityCheck(@RequestParam(value="username",required=true) final String username,@RequestParam(value="password",required=true) final String password,HttpServletRequest request)'

    '''
    method_str = 'public void getValue(String[] array) {'
    variables = get_method_param_variables(method_str)

    print(variables)

    #测试双引号元组集合
    
    #sql = 'dffff "select * from t where a="+ab+" and c="+cd+" and d="+fg'

    #col = find_quoatations(sql,'"')

    #print(col)

    #测试替换合法变量函数
    #row = 'admin.setNewadminName("123");admin=adminHistory'
    #variable = 'admin'
    #new_variable = 'a'
    #start = 0
    #row = replace_valid_varaibles(row,variable,new_variable,start)
    
    #print(row)

    #pattern = re.compile(r'for\((.*)\)')

    #row = 'for(int i=0;i<100;i++){'

    #match = pattern.search(row)

    #print(match.group(1))
    '''
