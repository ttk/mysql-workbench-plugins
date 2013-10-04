#
# Drupal query formatter for MySQL Workbench
#
# Created by Tom Kaminski (ttkaminski@gmail.com) 2013-10-03

from wb import DefineModule, wbinputs
import grt
import mforms
import re
from sql_reformatter import formatter_for_statement_ast, ASTHelper
from grt import log_info, log_error, log_warning, log_debug, log_debug2, log_debug3

# Define as a GRT module
ModuleInfo = DefineModule(name= "DrupalUtils", author= "Tom Kaminski (ttkaminski@gmail.com)", version="1.0")

##########################################

@ModuleInfo.plugin("wb.sqlide.stripTableBraces", caption = "Strip curly braces from table names", input=[wbinputs.currentQueryBuffer()], pluginMenu="SQL/Utilities")
@ModuleInfo.export(grt.INT, grt.classes.db_query_QueryBuffer)
def stripTableBraces(buffer):
  selectionOnly = True
  text = buffer.selectedText
  
  if not text:
    selectionOnly = False
    text = buffer.script
    
  text = re.sub(r'([ `]){([0-9,a-z,A-Z$_]+)}([ `])',r'\1\2\3',text)
    
  if selectionOnly:
    buffer.replaceSelection(text)
  else:
    buffer.replaceContents(text)

  mforms.App.get().set_status_text("Curly braces stripped from query")
  return 0
  
############################################
  
def get_table_ident_offsets(offsets,node):
  sym, val, children, base, begin, end = node
  if sym == "table_ident":
    node2 = children[0]
    sym2, val2, children2, base2, begin2, end2 = node2
    offsets.append((base2 + begin2, base2 + end2))
      
  for child in children:
    get_table_ident_offsets(offsets, child)
    
def transform_table_identifiers(sql,callable):
  from grt.modules import MysqlSqlFacade
  
  ast_list = MysqlSqlFacade.parseAstFromSqlScript(sql)
  
  # Do some validation first
  for ast in ast_list:
    if type(ast) is str:
      log_info("copyAsDrupalQuery",ast) # error
      mforms.App.get().set_status_text("Cannot format invalid SQL: %s" % ast)
      return 1
    #from sql_reformatter import dump_tree
    #import sys
    #myFile = open("C:\\temp\\log.txt", "w")
    #dump_tree(myFile, ast)
    #myFile.close()
    
  offsets = []
  for ast in ast_list:
    get_table_ident_offsets(offsets, ast)
   
  sql2 = ""    
  bb = 0   
  for b, e in offsets:
    sql2 += sql[bb:b] + callable(sql[b:e])
    bb = e
    
  sql2 += sql[bb:]
  return sql2
  
@ModuleInfo.plugin("wb.sqlide.copyAsDrupalQuery", caption= "Copy as Drupal query to clipboard", input= [wbinputs.currentQueryBuffer()], pluginMenu= "SQL/Utilities")
@ModuleInfo.export(grt.INT, grt.classes.db_query_QueryBuffer)
def copyAsDrupalQuery(buffer):
  sql = buffer.selectedText or buffer.script
  sql = transform_table_identifiers(sql,lambda s: "{" + s + "}")
  mforms.Utilities.set_clipboard_text(sql)
  mforms.App.get().set_status_text("Copied Drupal Query to clipboard")
  return 0