
Principles
==========

JigsawView is an alternative implementation to Django's generic Class
Based Views (called CBV later).

It has been created to manage some tedious work as CBV do but also
to be much more extensible. Our goal is to get somewhere between
generic CBV, the admin's classes and more flexibility.


JigsawView uses two major familly of classes. One is the view itself, the
other is a piece which can be a form, a formset or a model. You can use as many
pieces as you want in a view.


Unlike Django's generic CBV, a JigsawView isn't forced to have a particular
form of the Model. This means that with a single view class, you can:

- create a new instance
- update an instance
- delete an instance
- list all the instances
- view a particular instance


The way a Model is shown can be differed until the url resolution. For the
same reason, the template name will be altered according to how we represent
our Model.


