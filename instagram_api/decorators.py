# -*- coding: utf-8 -*-
from django.utils.functional import wraps
from django.db.models.query import QuerySet


def opt_arguments(func):
    '''
    Meta-decorator for ablity use decorators with optional arguments
    from here http://www.ellipsix.net/blog/2010/08/more-python-voodoo-optional-argument-decorators.html
    '''
    def meta_wrapper(*args, **kwargs):
        if len(args) == 1 and callable(args[0]):
            # No arguments, this is the decorator
            # Set default values for the arguments
            return func(args[0])
        else:
            def meta_func(inner_func):
                return func(inner_func, *args, **kwargs)
            return meta_func
    return meta_wrapper

@opt_arguments
def fetch_all(func, return_all=None, always_all=False):
    """
    Class method decorator for fetching all items. Add parameter `all=False` for decored method.
    If `all` is True, method runs as many times as it returns any results.
    Decorator receive parameters:
      * callback method `return_all`. It's called with the same parameters
        as decored method after all itmes are fetched.
      * `always_all` bool - return all instances in any case of argument `all`
        of decorated method
    Usage:

        @fetch_all(return_all=lambda self,instance,*a,**k: instance.items.all())
        def fetch_something(self, ..., *kwargs):
        ....
    """
    def wrapper(self, all=False, instances_all=None, **kwargs):
        response = {}
        instances = func(self, **kwargs)
        if len(instances) == 2 and isinstance(instances, tuple):
            instances, response = instances

        if always_all or all:
            if isinstance(instances, QuerySet):
                if instances_all is None:
                    instances_all = instances.none()
                instances_count = instances.count()
                if instances_count:
                    instances_all |= instances
            elif isinstance(instances, list):
                if instances_all is None:
                    instances_all = []
                instances_count = len(instances)
                instances_all += instances
            else:
                raise ValueError("Wrong type of response from func %s. It should be QuerySet or list, not a %s" % (func, type(instances)))

            next_url = response['pagination'].get('next_url', None)
            if next_url:
                return wrapper(self, all=True, next_url=next_url, instances_all=instances_all, **kwargs)

            if return_all:
                kwargs['instances'] = instances_all
                return return_all(self, **kwargs)
            else:
                return instances_all

        else:
            return instances

    return wraps(func)(wrapper)
