collective.behavior.sql
=======================

Overview
--------

collective.behavior.sql is a module intended to synchronize one or many sql databases with plone content using dexterity as content and sql table descriptor.

This module depends on sqlalchemy and z3c.saconnect to define the sql connections.


SQL Content Behavior
--------------------

After installing, a new behavior name "SQL Content" is available.
This behavior will allow you to choose the connection, source table and unique ID identifier (Primary Key) for your Dexterity SQL content.
After adding the SQL Content behavior, you will be able to specify wich column of the sql table corresponds to each field (existing or new) of your content type.

You can see all the data found in your SQL DB under the "Data" tab.
You can also specify a folder to act as container for the SQL items or add the SQL Dexterity content directly in plone like any other portal type and specify to which Primary Key your content corresponds. The module will the take data from the SQL DB for the specified fields.


Main features
----------

- All the configuration is done TTW, no need to code sql queries
- SQL datas can be added to the catalog like other standard content and therefore shown in search results, navigation, collections...
- SQL Behavior can handle relations between Dexterity SQL objects (RelationChoice, RelationList with one2many and many2many tables)
- SQL Dexterity items can be listed in a folder or added to the site like any other content
- Corresponding SQL column can be specified for both new fields and fields coming from other behaviors, so you can use SQL data for title, description, keywords, dates like effective, start end, ...


Limitations
-----------

At that time collective.behavior.sql cannot handle translations and workflow.
For the sql dexterity objects that are not added in the site (called virtual items) you will have to use a single state workflow set to "published".


Funding
-------

- `Idiap Research Institute <http://www.idiap.ch>`_, Martigny, Switzerland
- `Martronic SA <http://www.martronic.ch>`_, Monthey, Switzerland
