#
# Drupal schema generator for MySQL Workbench
#
# Originally created by Pedro Faria (2010)
# Edited and completed by zkday (2011)
# Cleaned up and upgraded for Drupal 7 by Matthijs (2012)
#

# Imports.
from wb import *
from mforms import Utilities
import mforms
import grt
import re

# Define this as a GRT module.
ModuleInfo = DefineModule(name='dumpDrupalSchema', author='Matthijs', version='1.2')

#
# Generate a drupal schema (including the hook) for the specified catalog.
#
@ModuleInfo.plugin('wb.catalog.util.dumpDrupalSchema', caption= 'Generate Drupal schema', input= [wbinputs.currentCatalog()], pluginMenu='Catalog')
@ModuleInfo.export(grt.INT, grt.classes.db_Catalog)
def GenerateDrupalSchema(catalog):
  output = ''

  # Add all tables.
  for schema in catalog.schemata :
    hook_created = False
    db_tables = {}

    for table in schema.tables :
      db_tables[(' %s ' % table.name)] = ' {%s} ' % table.name
      db_tables[(' %s.' % table.name)] = ' {%s}.' % table.name

    for table in schema.tables :
      if len(table.columns) > 0 :
        if not hook_created :
          ''' Create the hook '''
          if len(output) > 0 :
            output += "\n\n"

          output += "/**\n"
          output += " * Implements hook_schema().\n"
          output += " */\n"
          output += "function %s_schema() {\n" % re.sub(r'([^a-z0-9_]+|^[^a-z]+)', '', schema.name.lower().replace(' ', '_'))
          output += "  $schema = array();\n\n"
          hook_created = True

        ''' Add the table '''
        output += generateTableDefinition(table, db_tables)
        output += "\n"

    if hook_created :
      ''' Close the hook '''
      output += "  return $schema;\n"
      output += '}'

  if len(output) > 0 :
    # Should the output be copied to the clipboard?
    answer = Utilities.show_message('Copy to clipboard?', "Would you like to copy the schema to your clipboard?\nIt can also be viewed in the output window.", 'Yes', 'No', '')
    if answer == mforms.ResultOk :
      grt.modules.Workbench.copyToClipboard(output)

    # MySQL specific fields warning.
    if "'mysql_type' => '" in output :
      Utilities.show_message('MySQL specific fields used', 'Note that the schema definition contains MySQL specific fields!', 'OK', '', '')

    print output
  else :
    Utilities.show_warning('No valid tables found', 'The schema was not generated because no valid tables were found.', 'OK', '', '')

  return 0

#
# Generate the table definition for the specified table.
#
def generateTableDefinition(table, db_tables):
  primaryKeys, uniques, indexes = [], [], []

  # Collect all primary keys, uniques and indexes.
  for index in table.indices :
    if index.isPrimary :
      ''' Primary key '''
      for col in index.columns :
        primaryKeys.append("'%s'" % col.referencedColumn.name)

    elif index.unique :
      ''' Unique keys '''
      columns = []
      for col in index.columns :
        columns.append("'%s'" % col.referencedColumn.name)

      uniques.append("      '%s' => array(%s)" % (index.name, ', ' . join(columns)))
    else:
      ''' Indexes '''
      columns = []
      for col in index.columns :
        columns.append("'%s'" % col.referencedColumn.name)

      indexes.append("      '%s' => array(%s)" % (index.name, ', ' . join(columns)))

  # Create the table definition array.
  definition = "  $schema['%s'] = array(\n" % table.name

  # Table description.
  if table.comment:
    definition += "    'description' => '%s',\n" % table.comment.replace("'", "\'").strip()

  # Add all columns.
  definition += "    'fields' => array(\n"

  for column in table.columns :
    definition += generateFieldDefinition(column, db_tables)

  definition += "    ),\n"

  # Add the primary key.
  if len(primaryKeys) :
    definition += "    'primary key' => array(%s),\n" % ", " . join(primaryKeys)

  # Add all indexes.
  if len(indexes) :
    definition += "    'indexes' => array(\n%s,\n    ),\n" % ",\n" . join(indexes)

  # Add all uniques.
  if len(uniques) :
    definition += "    'unique keys' => array(\n%s,\n    ),\n" % ",\n" . join(uniques)

  # Close the table defenition array.
  definition += "  );\n"

  return definition

#
# Generate the field definition array for the specified column.
#
def generateFieldDefinition(column, db_tables) :
  specs = []

  # Get the column type.
  p = re.search('([a-z]+)(?:\(([0-9]+)\))?', column.formattedType.lower())
  type = p.group(1)

  # Convert the column type.
  if type.endswith('int') :
    ''' Integer '''
    if type == 'tinyint' :
      specs.append("'size' => 'tiny'")
    elif type == 'smallint' :
      specs.append("'size' => 'small'")
    elif type == 'mediumint' :
      specs.append("'size' => 'medium'")
    elif type == 'bigint' :
      specs.append("'size' => 'big'")
    else :
      specs.append("'size' => 'normal'")

    if column.autoIncrement :
      type = 'serial';
    else :
      type = 'int'
  elif type == 'float' or type == 'double' :
    ''' Float '''
    if type == 'double' or column.scale >= 10 or (column.precision > 25 and column.scale == -1) :
      specs.append("'size' => 'big'")
    elif column.scale >= 6 or (column.precision >= 16 and column.scale == -1) :
      specs.append("'size' => 'medium'")
    elif column.scale >= 3 or (column.precision >= 8 and column.scale == -1) :
      specs.append("'size' => 'small'")
    else :
      specs.append("'size' => 'tiny'")

    type = 'float'
  elif type == 'numeric' or type == 'decimal' :
    ''' Numeric '''
    if column.scale > -1 and column.precision > -1 :
      specs.append("'scale' => %d" % column.scale)
      specs.append("'precision' => %d" % column.precision)
    else :
      specs.append("'scale' => 5")
      specs.append("'precision' => 2")

    type = 'numeric'
  elif type.endswith('text') :
    ''' Text '''
    if type == 'tinytext' :
      specs.append("'size' => 'tiny'")
    elif type == 'mediumtext' :
      specs.append("'size' => 'medium'")
    elif type == 'longtext' :
      specs.append("'size' => 'big'")
    else :
      specs.append("'size' => 'normal'")

    if column.length > -1 :
      specs.append("'length' => %d" % column.length)

    type = 'text'
  elif type.endswith('char') :
    ''' (Var)char '''
    specs.append("'length' => %d" % column.length)
  elif type.endswith('blob') :
    ''' Blob '''
    if type == 'longblob' :
      specs.append("'size' => 'big'")
    else :
      specs.append("'size' => 'normal'")
  elif type.startswith('date') :
    ''' Datetime '''
    type = 'datetime'
    specs.append("'mysql_type' => 'datetime'")
    specs.append("'pgsql_type' => 'timestamp without time zone'")
    specs.append("'sqlite_type' => 'varchar'")
    specs.append("'sqlsrv_type' => 'smalldatetime'")
  else :
    ''' MySQL-only type '''
    specs.append("'mysql_type' => '%s'" % type)
    type = 'text'
    specs.append("'size' => 'normal'")

  # Insert the field type.
  specs.insert(0, "'type' => '%s'" % type)

  # Unsigned or binary?
  for flag in column.flags :
    if flag == 'UNSIGNED' :
      specs.append("'unsigned' => TRUE")
      break
    elif flag == 'BINARY' :
      specs.append("'binary' => TRUE")
      break

  # Not null?
  if column.isNotNull :
    specs.append("'not null' => TRUE")

  # Default value.
  if not column.defaultValueIsNull and column.defaultValue :
    if column.defaultValue.isdigit() :
      specs.append("'default' => %s" % column.defaultValue)
    else :
      specs.append("'default' => '%s'" % column.defaultValue.replace("'", "\'"))

  # Description.
  if column.comment :
    comment = ' ' + column.comment.replace("'", "\'") + ' '

    for key, value in db_tables.iteritems() :
      comment = comment.replace(key, value)

    specs.append("'description' => '%s'" % comment.strip())

  # Create the field defenition array.
  definition = "      '%s' => array(\n" % column.name

  # Add all specifications.
  for item in specs :
    definition += "        %s,\n" % item

  # Close the field definition array.
  definition += "      ),\n"

  return definition