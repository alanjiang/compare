# -*- coding: utf-8 -*
import difflib
import sys
import argparse
import os
import re
from method_mark import *
from htmltool import *



#result_report=result_folder+'/report/report.txt'
#ratio_file=result_folder+'/report/ratio.txt'
#diff_lines_file=result_folder+'/report/difflines.txt'
#diff_method_file=result_folder+'/report/diffmethods.txt'



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
# 读取文件所有的行
def read_file(file_name):
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
    print ("正在比较文件{0} 和 {1}".format(file1, file2))
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

   #file1
   dic_file_methods_1=findMethods(dic_class_body_1[file1],file1)

   dic_file_methods_1=injectMethodLineNumbers(file1,dic_file_methods_1)

   #file2
   dic_file_methods_2=findMethods(dic_class_body_2[file2],file2)

   dic_file_methods_2=injectMethodLineNumbers(file2,dic_file_methods_2)

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
                content1=getCodeByRowNumbers(code_dic1,marker1.start,marker1.end)
                content2=getCodeByRowNumbers(code_dic2,marker2.start,marker2.end)
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

    return content1 == content2
    


    
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

    print('<====报告生成完毕====>')
            
#需要考虑:implements,extends情况,获取类的内容{}中间的部分   
def findClassBody(file):

    dic={}

    fopen = open(file, 'r')

    fileread = fopen.read()

    #print(fileread)
    pattern=re.compile(r'\s+public\s+class\s+[A-Za-z0-9_]+\s+[implements|extends]*\s+[A-Za-z0-9<>,]+\s*\{([\s\S]*)|\s+public\s+class\s+[A-Za-z0-9_]+\s*\{([\s\S]*)')
    
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
    result=re.findall(r'(p[a-z]{5,8}\s+.*?{)',dic_class_body.replace('\n',LINE_SHIFT),re.M)

    #result1=re.findall(r'(\s*private\s+.*^;?\{)',dic_class_body.replace('\n',LINE_SHIFT))
    #print('==>1所有的 method {}'.format(result1))
    #result=re.findall(r'(\s+public\s+[0-9A-Za-z]{1,}\s+[0-9A-Za-z]{1,}\s*\(.*\)\s*[.~]*?\{)',dic_class_body.replace('\n',LINE_SHIFT))
    #result=re.findall(r'(public\s*.*?\{|protected\s+.*?\{|private\s+.*?\{)',dic_class_body.replace('\n',LINE_SHIFT))
    #result=re.findall(r'((?:public|protected)+\s+.*?\(.*\)\s+.*\{)',dic_class_body.replace('\n',LINE_SHIFT))
    
    #print('==>所有的 method {}'.format(result))

    
    dic={} #文件的方法字典,key:文件路径,value: MethodMarker
   

    method_markers=[] #MethodMarker集合
    

    for method_str in result:
        
        
        pattern='(?P<method>[a-zA-Z_]{1,})\(.*\)'

        res=re.search(pattern,method_str)

        if res is None:

           continue
        
        
        else:
           method=res.group('method')
           method_str_rows=len(method_str.split(LINE_SHIFT))
           
           if (not method_str.replace(LINE_SHIFT,'').strip().endswith('{')) or method_str.replace(LINE_SHIFT,'').find('class') !=-1 or method_str.replace(LINE_SHIFT,'').find(';') !=-1 or  ( method_str.replace(LINE_SHIFT,'').strip().find('(') ==-1 or method_str.replace(LINE_SHIFT,'').strip().find(')') ==-1 ):

                print('=>method:{} not valid,ignore'.format(method))

           else :

               methodMarker=MethodMarker(method,method_str,method_str_rows,0,0) #方法标记
           
               method_markers.append(methodMarker)
                  
            
               
    
    #for methodMarker in method_markers:

       #print('===>methodMarker,method:{}'.format(methodMarker.method))
       #print('===>methodMarker,method_str:{}'.format(methodMarker.method_str))
       #method_str_rows=len(methodMarker.method_str.split(LINE_SHIFT))
       #print('===>methodMarker,method_str size:{}'.format(method_str_rows))
        
    dic[file]=method_markers

    return dic #返回字典


#标记方法体的起、始行号，方法体内容更可靠

#file: 文件的绝对路径, dic:(key:文件路径,value:MethodMarker[]) 

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
             if line == '' or line.strip() =='{' or line.strip() == LINE_SHIFT : #空行和单独的{不比较
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

    #str=getCodeByRowNumbers(code_dic,1,200)

    #print('==>getCodeByRowNumbers:{}'.format(str))
    
    removeNeiborElements(numbers)

    #print('===>移除相差1的元素，保留最少的数作为特征行的行号后元素<=====')
    for number in numbers:

        print(number)

    if (len(numbers)-1) < numberOfMethodMarker: #不正确

        numberOfMethodMarker=len(numbers)-1
        

    for index in range(0,numberOfMethodMarker): 

      #print('===>index={}'.format(index))
      if (index+1) <= numberOfMethodMarker:
         methodMarkers[index].start=numbers[index]
      
         methodMarkers[index].end=numbers[index+1]-1
      
         
    if (len(numbers)-1) == numberOfMethodMarker:
        cleanMethodMarkers(methodMarkers,code_dic)
    
    print('====>重置起始行并清洗最后一行后，方法标记对象值<====')
    for marker in methodMarkers:

      #print('==>start:{},end:{}'.format(marker.start,marker.end))
      
      str=getCodeByRowNumbers(code_dic,marker.start,marker.end)

      #print('==>方法 {}, 函数体:{}'.format(marker.method,str))
   
    dic[file]=methodMarkers # 更新字典，将新的方法标记对象List作为value

    return dic 


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
   


    
'''
旧的和新的比较,有以下结果：
1) 旧的类中的方法在新的类中找不到：删除

2) 旧的类中的方法在新的类中可以找到，但内容不相同： 修改了

3) 新的类中有的方法在旧的类中没有：新增

'''


if __name__ == "__main__":


    result_folder='/Users/zhangxiao/agilean/valuekanban/python-anti-compile/dest/result'
    diff_html_file=result_folder+'/report/report.html'
    
    folder1='/Users/zhangxiao/agilean/valuekanban/python-anti-compile/dest.back'#反编译
    
    folder2='/Users/zhangxiao/agilean/valuekanban/python-anti-compile/dest2.back'
    

    #系统参数传入
    '''
    result_folder=sys.argv[1]

    diff_html_file=result_folder+'/report/report.html'

    folder1=sys.argv[2]

    folder2=sys.argv[3]
    '''
    #生成报告
    genReport(folder1,folder2,result_folder,diff_html_file)

    print('<===报告Done==>')

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
    

