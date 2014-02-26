FAQ
===

Q: Adding a **nullable=False** column
**************************************

A: Your table probably already contains data. That means if you add column, it's contents will be NULL.
Thus adding NOT NULL column restriction will trigger IntegrityError on database level.

You have basically two options:

#. Add the column with a default value and then, after it is created, remove the default value property. This does not work for column types that do not allow default values at all (such as 'text' and 'blob' on MySQL).
#. Add the column without NOT NULL so all rows get a NULL value, UPDATE the column to set a value for all rows, then add the NOT NULL property to the column. This works for all column types.
