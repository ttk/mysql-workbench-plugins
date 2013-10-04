Plugins for MySQL Workbench
=======================

I created a MySQL Workbench plugin that makes it easier when testing/writing queries during drupal module development.  After installing the plugin, it adds two menu options (In the SQL Editor View):

    Plugins->Utilities->Strip curly braces from table names
    Plugins->Utilities->Copy as Drupal query to clipboard

The first command removes the curly braces from around table names. eg.
    SELECT * FROM {users};  => SELECT * FROM users;

The second command does the opposite and copies the result to the clipboard:
    SELECT * FROM users;  => SELECT * FROM {users};

Known limitations:
* Does not handle table prefixes - it's maybe possible to auto-detect this from the existing tables names
* Curly braces may be stripped if they occur in a string value.  This is a rare occurance.
