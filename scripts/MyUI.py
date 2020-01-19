# -*- coding: utf-8 -*

import datetime


import tkinter as tk
from tkinter.filedialog import askdirectory

import tkinter.messagebox



#python线程
import threading
import time
import inspect
import ctypes
#python线程
#import pickle
import os
#导入文件比较主程
#from batch_beyond_compare import *
from function_extract import *
#导入反编译主程
from batch_decompiler import *
import rewrite_tool as writer

from tkinter.constants import END
from tkinter import scrolledtext
from tkinter.constants import RIGHT, LEFT, Y, BOTH

#folder1=None
#folder2=None
#submitBtn=None

#infoLabel=None

#typeChoose=None

#compilerChoose=None #选择哪个反编译工具

TASK='task'


#window=tk.Tk()

global window
global scrText


class MyThread(threading.Thread):

     
     def __init__(self,folder1,folder2,typeChoose,compilerChoose,myUI):
         super().__init__()
         self.folder1=folder1
         self.folder2=folder2
         self.typeChoose=typeChoose
         self.compilerChoose=compilerChoose
         self.myUI = myUI
   

          
     def run(self):

         
         start = datetime.datetime.now() #获得当前时间
         
         #doTask(folder1,folder2,typeChoose,compilerChoose)
         threading.current_thread().name=TASK #线程标识

         current_folder=os.getcwd()
    
         fd1=current_folder+'/report/dest1'

         fd2=current_folder+'/report/dest2'
       
         result_folder=os.getcwd()+'/report'


         if typeChoose.get() == 1: #基于classes比较，先需要反编译
            #仅反编译才需要备份
            self.myUI.writeLog('开始执行备份')
            self.myUI.backUp(result_folder,fd1,fd2)
            self.myUI.writeLog('已成功备份')
            self.myUI.writeLog('--folder1:{},folder2:{} 执行反编译'.format(folder1.get(),folder2.get()))
            batch_decompile(folder1.get(),folder2.get(),compilerChoose.get())
            self.myUI.writeLog('==> 将反编译的文件还原到指定的包中,分别移动{},{}两个文件夹中的文件 <=='.format(fd1,fd2))
            #只是移动了反编译后的JAVA源文件，将fd1, fd2 别为反编译后的.java文件夹
            placeJavaFileList(fd1,fd1)
            placeJavaFileList(fd2,fd2)
            #将folder1.get()指定的目录拷贝到dest1中
            self.myUI.writeLog('=>将{}拷贝至{}'.format(folder1.get(),fd1+'/project'))
            moveFolder(folder1.get(),fd1+'/project')
            self.myUI.writeLog('=>将{}拷贝至{}'.format(folder2.get(),fd2+'/project'))
            moveFolder(folder2.get(),fd2+'/project')
            
            self.myUI.writeLog('反编译完成')
         
         else:
             
            self.myUI.writeLog('==>选择基于源码比较，跳过反编译步骤<===')
         
         diff_html_file=result_folder+'/report.html'
           
         if not os.path.exists(result_folder):

            os.makedirs(result_folder) #创建report

         if not os.path.exists(diff_html_file):

           f = open(diff_html_file,'w')

           f.close()
         self.myUI.writeLog('删除html历史文件....')
         del_report(result_folder)
         self.myUI.writeLog('==>执行比较<===')
         if typeChoose.get() == 1:

           self.myUI.writeLog('=>已完成反编译，输出java文件至:{},{}'.format(fd1,fd2))
           tpl = writer.new_folder( fd1,fd2)
           self.myUI.writeLog('=>生成原生产源码：{}的副本{} , master源码:{}的副本{} '.format(fd1,fd2,tpl[0],tpl[1]))
           self.myUI.writeLog('=>原生产源码：{}, master源码:{}将保持反编译原样输出不变，将对生产副本{},master副本{}进行分析处理 '.format(fd1,fd2,tpl[0],tpl[1]))
           mself.myUI.genReport(tpl[0],tpl[1],result_folder,diff_html_file)
      
         else:
          self.myUI.writeLog('=>跳过反编译,用户选取了生产源码位于：{}, master源码位于:{}'.format(folder1.get(),folder2.get()))
          tpl = writer.new_folder( folder1.get(),folder2.get())
          self.myUI.writeLog('=>生成原生产源码：{}的副本{} , master源码:{}的副本{} '.format(fd1,fd2,tpl[0],tpl[1]))
          self.myUI.writeLog('=>原生产源码：{}, master源码:{}保持不变，将对:{},{}进行分析处理 '.format(folder1.get(),folder2.get(),tpl[0],tpl[1]))
          genReport(tpl[0],tpl[1],result_folder,diff_html_file)
      
         self.myUI.writeLog('文件比较完成')

         try:
           
           rewriteReport(diff_html_file)

         except Exception as e:

            self.myUI.writeLog('重写报告异常，但不影响报告的正确性，异常部分如下：')
            self.myUI.writeLog(e)
         
         self.myUI.writeLog('重写报告完成')
         
         self.myUI.writeLog('报告结果位于：{}'.format(diff_html_file))

         self.myUI.writeLog('===>爬虫主程结束，报告位于：{}<=========='.format(diff_html_file))

         end= datetime.datetime.now() #获得当前时间

         diff_time = (end-start).seconds/60

         self.myUI.writeLog('总共耗时：{}分钟'.format(diff_time))

         self.myUI.writeLog('********************')

         self.myUI.writeLog('*****Good Bye!******')

         self.myUI.writeLog('********************')
        


class MyUI:

  
    
  def __init__(self,window,scrText):
       self.launchWindow (window,scrText)

  '''    
  def __init__(self,window,scrText):

      self.window = window
      self.scrText = scrText
      self.launchWindow (window,scrText)
  '''     

  def launchWindow (self,window,scrText):
    
    global folder1
    global folder2
    global submitBtn
    global exitBtn
    global msg
    global typeChoose
    global compilerChoose
    global thread
    
  
    #窗口
    width=700
    height=420
    print(tk)
    typeChoose=tk.IntVar()
    typeChoose.set(1)
    compilerChoose=tk.IntVar()
    compilerChoose.set(3)
    tk.Radiobutton(window,text="基于classes文件夹比较", variable=typeChoose, value=1).place(x=16,y=50)

    tk.Radiobutton(window,text="基于源码比较", variable=typeChoose, value=2).place(x=240,y=50)

    #采用何种反编译工具

    tk.Radiobutton(window,text="jad工具", variable=compilerChoose, value=1).place(x=16,y=85)

    tk.Radiobutton(window,text="procyon工具", variable=compilerChoose, value=2).place(x=180,y=85)


    tk.Radiobutton(window,text="fernflower工具(推荐)", variable=compilerChoose, value=3).place(x=360,y=85)
    
    #标签 
    tk.Label(window,text='生产版本(含编译文件)路径:').place(x=6,y=110)
    tk.Label(window,text='master版本(含编译文件)路径：').place(x=6,y=150)
    #folder1
    folder1=tk.StringVar()
    msg=tk.StringVar()
    entry_folder1=tk.Entry(window,textvariable=folder1)
    entry_folder1.place(x=200,y=110,width=320)
    #folder2
    folder2=tk.StringVar()
    
    entry_folder2=tk.Entry(window,textvariable=folder2)
    entry_folder2.place(x=200,y=150,width=320)

    

    #文件选择按钮
    tk.Button(window,text='浏览...',command=self.selectDirectory1).place(x=525,y=110);
    tk.Button(window,text='浏览...',command=self.selectDirectory2).place(x=525,y=150);


    #提交按钮
    submitBtn=tk.Button(window,text='开始运行',bg='green',command=self.submit)

    submitBtn.place(x=260,y=185)


    pauseBtn=tk.Button(window,text='暂停运行',bg='red',command=self.exit)


    pauseBtn.place(x=420,y=185)
    
    #print('===>2,submitBtn:{}'.format(submitBtn))
    
    screenwidth = window.winfo_screenwidth()
    screenheight = window.winfo_screenheight()

    size = '%dx%d+%d+%d' % (width, height, (screenwidth - width)/2, (screenheight - height)/2)
    

    #scrText.pack(fill=BOTH, side=LEFT, expand=True)
    
    
    
    '''
    for i in range(0,12):

      time.sleep(3)
      scr.insert(END,'Hello World')
    '''
    window.geometry(size)

    window.mainloop()
  #反编译的成果备份
  def backUp(self,result_folder,fd1,fd2):
         time_stamp = time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))

         if os.path.exists(result_folder): 

            os.rename(result_folder,result_folder+'-'+time_stamp)#重命名
            
            os.makedirs(result_folder) #创建report
            
            os.makedirs(fd1)

            os.makedirs(fd2) 
            
         else: #不存在
            os.makedirs(result_folder)
            os.makedirs(fd1)
            os.makedirs(fd2) 
            
  def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")
    #print('当前线程成功终止')
 
  def stop_thread(thread):
    
    _async_raise(thread.ident, SystemExit)





  def selectDirectory1(self):

    str=askdirectory()
    
    #print('==>choose path:{}'.format(str))
    #print(type(str))
    if str != ' ':
      folder1.set(str)
    

  def selectDirectory2(self):

    str=askdirectory()
    #print('==>choose path:{}'.format(str))
    if str != ' ':
       folder2.set(str)

  #退出运行主程
  def exit(self):

    
    #thread=threading.current_thread()
    #print('==>1,current thread:{}'.format(thread))
    #thread=threading.current_thread()
    #print('==>2,current thread:{}'.format(thread))

    
         
    if killTask() :
     
       print('当前线程成功终止')
       tk.messagebox.showinfo('提示','已执行终止指令')
    

  def killTask(self):

   for item in threading.enumerate():
         #print('=>item:{},type:{}'.format(item,type(item)))
         #print(item.name)
         if item.name == TASK:

            stop_thread(thread)
            return True
            
   return False


  def submit(self):


   if folder1.get() == '':

      tk.messagebox.showinfo('错误提示','请输入生产编译文件路径')

      return 'FAIL'
   
   if folder2.get() == '':

      tk.messagebox.showinfo('错误提示','请输入mater编译文件路径')

      return 'FAIL'

   if not self.isValidFolder(folder1.get()):

     tk.messagebox.showinfo('错误提示','生产编译文件路径不存在')

     return 'FAIL'

   if not self.isValidFolder(folder2.get()):

     tk.messagebox.showinfo('错误提示','mater编译文件不存在')

     return 'FAIL'
   '''
   if typeChoose.get() == 1: #基于classes比较，先需要反编译

      if not folder1.get().endswith('classes'):

          tk.messagebox.showinfo('错误提示','请确保旧版本的classes文件夹以classes结尾')

          return 'FAIL'
      if not folder2.get().endswith('classes'):

          tk.messagebox.showinfo('错误提示','请确保新版本的classes文件夹以classes结尾')

          return 'FAIL'
   '''
   
   #thread = threading.Thread(target=doTask, args=(folder1,folder2,typeChoose,compilerChoose))

   #thread.start()

   print('===>thread active_count:{}'.format(threading.active_count()))
   if not self.taskIsRunning() :
      thread=MyThread(folder1,folder2,typeChoose,compilerChoose,self)

      thread.start()
   
   else:

       print('==>当前已有运行线程<==')

  #检查有无TASK名称的线程在运行状态
  def taskIsRunning(self):

     for item in threading.enumerate():
         print('=>item:{},type:{}'.format(item,type(item)))
         print(item.name)
         if item.name == TASK:

            return True
     return False
           
 
  
    

  #flag: disabled
  def resetSubmitBtn(self,msg,flag):

   #global submitBtn
   #global window
   
   submitBtn=tk.Button(window,text=msg,bg='red',state=flag)
   submitBtn.place(x=260,y=180)

  
  def writeLog (self,msg):
   
    
     global scrText
     
     self.scrText.insert(END,'\n\t'+msg)
     self.scrText.see(END)
     #scrText.focus_set()
     content = self.scrText.get('1.0', 'end-1c')
     if len(content.splitlines()) == 10:
        self.scrText.delete(1.0, END)
        

  @staticmethod
  def writeLog (msg):
   
    
     
     
     scrText.insert(END,'\n\t'+msg)
     scrText.see(END)
     #scrText.focus_set()
     content = scrText.get('1.0', 'end-1c')
     if len(content.splitlines()) == 10:
        scrText.delete(1.0, END)
        
  def isValidFolder (self,folder):

    #print('===>isValid:{}'.format(os.path.exists(folder)))

    return os.path.exists(folder)


  def getStrLength(str):

    return len(str.split(','))

  #插入报告部分start
  def rewriteReport(self,fileName):
    #lines = read_file(fileName) #文件所有的行
    #code_dic=getCodeDic(lines) #文件所有的行字典，key:行号,value:行内容

    file= open(fileName, 'r',encoding='utf-8')
    #text = file.read().splitlines()
    text = file.read()
    file.close()
    
    pattern='<tr><th>类名</th><th>行改动位置</th></tr>(?P<body>.*)</table>'

    res=re.search(pattern,text,re.M)

    collection = []

    # <td><a href="./com.hanniu.dian.test.redis.RedisTestBean.java.html" target="_blank">
    #/Users/zhangxiao/Desktop/source/dian-old/dian-web/src/test/java/com/hanniu/dian/test/redis/RedisTestBean.java</a></td>
    if res:
           body=res.group('body')
     
           #print(len(body))

           list = re.findall(r'<tr><td><a\s+href=\"\.\/[a-zA-Z0-9._\s$\-]+\"\s+target=\"_blank\">([0-9A-Za-z.:_$\\\-\/\u4e00-\u9fcc\s]+?)</a></td><td>([0-9,]+?)</td></tr>',body,re.S)
           #print(list)
           for item in list:

               tpl = (item[0],item[1],getStrLength(item[1]))
               #print(tpl)
               collection.append(tpl)
          
    if len(collection) > 0:

        #lambda函数排序
        collection  = sorted(collection,key=lambda x: (x[2])
                             )      

    insertTable = '<p style="color:red">java文件比较行改动行数统计</p><table class="gridtable"><tr><th>java文件</th><th>更新行数</th></tr>'

    level1 = 0

    level2 = 0

    level3 = 0

    total = len(collection)

    if total == 0:

        return 'EXIT'
    
    for tp in collection:


        if getStrLength(tp[1]) <= 10:
            
            insertTable+='<tr><td>'+genLink(tp[0])+'</td><td style="background:green;">'+str(getStrLength(tp[1]))+'</td></tr>'
            level1+=1
        elif getStrLength(tp[1]) > 10 and getStrLength(tp[1]) < 30:
            insertTable+='<tr><td>'+genLink(tp[0])+'</td><td style="background:yellow;">'+str(getStrLength(tp[1]))+'</td></tr>'
            level2+=1
        else:    
            insertTable+='<tr><td>'+genLink(tp[0])+'</td><td style="background:red;">'+str(getStrLength(tp[1]))+'</td></tr>'
            level3+=1


    ratio1 = '{:.2%}'.format(level1/total )

    ratio2 = '{:.2%}'.format(level2/total )

    ratio3 = '{:.2%}'.format(level3/total )
    
          
    insertTable+='</table>'

    insertTable+= '<p style="color:red">java文件比较改动级别统计</p><table class="gridtable"><tr><th>改动级别</th><th>文件个数</th><th>占比</th></tr>'
    insertTable+='<tr><td>改动10行以下</td><td style="background:green;">'+str(level1)+'</td><td style="background:green;">'+ratio1+'</td></tr>'
    insertTable+='<tr><td>改动30行以下</td><td style="background:yellow;">'+str(level2)+'</td><td style="background:yellow;">'+ratio2+'</td></tr>'

    insertTable+='<tr><td>改动30行以上</td><td style="background:red;">'+str(level3)+'</td><td style="background:red;">'+ratio3+'</td></tr>'

    insertTable+='</table>'
    
    #print('=>insertTable:{}'.format(insertTable))
    pos = text.find('</body>')

    
    
    insertText(fileName,pos,insertTable,text)


    



  #插入文本text
  def insertText(fileName,pos,text,fileContent):


   with open(fileName,'wt',encoding='utf-8') as file:
       
        content=fileContent[:pos]+text+fileContent[pos:]
        
        file.writelines(content)
    

  #插入报告部分end




  def del_report(filepath):

    
    fileNames = os.listdir(filepath)  # 获取当前路径下的文件名，返回List
    for file in fileNames:
        newDir = filepath + '/' + file
        
        # if os.path.isdir(newDir): # 如果是文件夹
        if os.path.isfile(newDir):  # 如果是文件
            #print(newDir)
            #print(os.path.splitext(newDir)[1])
            if os.path.splitext(newDir)[1] == ".html":  # 判断是否是.html
            
                if not newDir.endswith('report.html'):

                   try:

                     os.remove(newDir)
                   except Exception as e:

                      self.writeLog('warning:删除 :{}文件出错，请确保文件没有占用'.format(newDir))
                
        
        

if __name__ == "__main__":
    global scrText
    window=tk.Tk()
    window.title('python反编译比较工具V4.0, Grow Together!')
    scrText = scrolledtext.ScrolledText(window,width=200,height=40)
    scrText.place(x=20,y=240)
    

    win = MyUI(window,scrText)
    
   
   
    
           



     
