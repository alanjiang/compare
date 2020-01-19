# -*- coding: utf-8 -*
class MethodMarker :
    '''
     method: 方法名称
     method_str: 方法特征字符串,回车行已处理
     method_str_rows: 方法特征字符串行数,{结束
     start: 方法体的起始行
     end:  方法的结束行位置
     body: 方法体内容
     variables: list集合，方法中的变量, [('变量名1','变量类型','empty|final',[(第几行,出现次数,...]),...] 新增数据结构
     params: [] 方法参数的集合，按出现的先后顺序 [('map','Map',None,'') , ('employeeNo','String',None,'final')
     method_no_param: 没有参数的方法,只显示类型，如： say(String msg) = > say(['String']) 
    '''
    def __init__(self, method, method_str, method_str_rows, start, end,body,variables, params,method_no_param):
        
        self.method = method
        self.method_str=method_str
        self.method_str_rows=method_str_rows
        self.start = start
        self.end = end
        self.body=body
        self.variables = variables
        self.params = params
        self.method_no_param = method_no_param
   
