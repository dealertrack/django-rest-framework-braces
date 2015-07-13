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


def add_base_class_to_instance(instance, base_class=None, new_name=None):
    """
    Generic utility for adding a base class to an instance.

    This function returns a copy of the given instance which
    will then include the new base_class in its ``__mro__``.

    The way that is done internally is it creates a brand new
    class with correct bases. Then the newly created class is
    instantiated. Since ``__init__`` could be expensive operation
    in any of the base classes of the original instance mro,
    nto make it cheap, we temporarily switch __init__ with
    super simple implementation which does nothing but only
    instantiates class. Once instantiated, then we copy all of the
    instance attributes to the newly created instance.
    Finally, then we pop our mock ``__init__`` implementation.

    Args:
        instance (object): Instance of any object
        base_class (type): Any class which will be added as first class
            in the newly copied instance mro.

    Returns:
        Shallow copy of ``instance`` which will also inherit ``base_class``.
    """
    # overwrite __init__ since that is mainly responsible for setting
    # instance state but since we explicitly copy it, we can
    # make __init__ a noop method
    def __init__(self, *args, **kwargs):
        pass

    if base_class is not None and base_class not in instance.__class__.mro():
        base_classes = (base_class, instance.__class__)
    else:
        base_classes = (instance.__class__,)

    new_field_class = type(
        str(new_name or instance.__class__.__name__),
        base_classes,
        {'__init__': __init__}
    )

    new_instance = new_field_class()
    new_instance.__dict__.update(instance.__dict__)

    # we added __init__ just for faster instantiation
    # since then we dont have to copy all the parameters
    # when creating new instance and then update its state
    # however after we instantiated the class, we want to
    # pop our silly __init__ implementation so that if somebody
    # wants to instantiate instance.__class__(), it will
    # use the original __init__ method
    del new_field_class.__init__

    return new_instance


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
    """
    Generates new name by replacing the existing suffix with a new one.

    Args:
        klass (type): original class from which new name is generated
        existing_suffix (str): the suffix which needs to remain where it is
        new_suffix (str): the new suffix desired

    Example:
        >>> get_class_name_with_new_suffix(FooForm, 'Form', 'NewForm')
        'FooNewForm'

    Returns:
        new_name (str): the name with the new suffix
    """
    class_name = klass.__name__

    if existing_suffix in class_name:
        prefix, suffix = class_name.rsplit(existing_suffix, 1)
    else:
        prefix, suffix = class_name, ''

    new_name = str('{}{}{}'.format(prefix, new_suffix, suffix))

    return new_name


def get_attr_from_base_classes(bases, attrs, attr, default=None):
    """
    The attribute is retrieved from the base classes if they are not already
    present on the object.

    Args:
        bases (tuple, list): The base classes for a class.
        attrs (dict): The attributes of the class.
        attr (str): Specific attribute being looked for.
        default (any): Whatever default value is expected if the
            attr is not found.

    Returns:
        attribute value as found in base classes or a default when attribute
        is not found and default is provided.

    Raises:
        AttributeError: When the attribute is not present anywhere in the
            call chain hierarchy specified through bases and the attributes
            of the class itself
    """
    if attr in attrs:
        return attrs[attr]

    for base in bases:
        try:
            return getattr(base, attr)
        except AttributeError:
            continue

    if default is not None:
        return default

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
