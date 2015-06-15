from __future__ import print_function, unicode_literals
import inspect
import itertools


IGNORE_ARGS = ['self', 'cls']


def find_function_args(func):
    """
    Get the list of parameter names which function accepts.
    """
    try:
        spec = inspect.getargspec(func)
        return [i for i in spec[0] if i not in IGNORE_ARGS]
    except TypeError:
        return []


def find_class_args(klass):
    """
    Find all class arguments (parameters) which can be passed in ``__init__``.
    """
    args = set()

    for i in klass.mro():
        if i is object or not hasattr(i, '__init__'):
            continue
        args |= set(find_function_args(i.__init__))

    return list(args)


def find_matching_class_kwargs(reference_object, klass):
    return {
        i: getattr(reference_object, i) for i in find_class_args(klass)
        if hasattr(reference_object, i)
    }


def initialize_class_using_reference_object(reference_object, klass, **kwargs):
    """
    Utility function which instantiates ``klass`` by extracting ``__init__``
    kwargs from ``reference_object`` attributes.

    Args:
        reference_object (object): Any object instance from which matching
            attributes will be used as ``klass``'s ``__init__`` kwargs.
        klass (type): Class which will be instantiated by using
            ``reference_object`` attributes.
        **kwargs: Any additional kwargs which will be passed during instantiation.

    Returns:
        Instantiated ``klass`` object.
    """
    _kwargs = find_matching_class_kwargs(reference_object, klass)
    _kwargs.update(kwargs)

    return klass(**_kwargs)


def get_class_name_with_new_suffix(klass, existing_suffix, new_suffix):
    class_name = klass.__name__

    if existing_suffix in class_name:
        prefix, suffix = class_name.rsplit(existing_suffix, 1)
    else:
        prefix, suffix = class_name, ''

    new_name = str('{}{}{}'.format(prefix, new_suffix, suffix))

    return new_name


def get_attr_from_base_classes(bases, attrs, attr, **kwargs):
    if attr in attrs:
        return attrs[attr]

    for base in bases:
        try:
            return getattr(base, attr)
        except AttributeError:
            continue

    if 'default' in kwargs:
        return kwargs['default']

    raise AttributeError(
        'None of the bases have {} attribute'
        ''.format(attr)
    )


def reduce_attr_dict_from_base_classes(bases, getter, default=None):
    data = (default or {}).copy()

    # get all field mappings from super methods
    for base in itertools.chain(*[reversed(i.mro()) for i in reversed(bases)]):
        data.update(getter(base) or {})

    return data


def reduce_attr_dict_from_instance(self, getter, default=None):
    data = reduce_attr_dict_from_base_classes(type(self).mro(), getter, default)

    # this should of been picked by reduce_attr_dict_from_base_classes
    # however that only accounts base classes and not instance
    # attribute which can be modified in __init__, etc so we
    # explicitly account for it
    data.update(getter(self) or {})

    return data
