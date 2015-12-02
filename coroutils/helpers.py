import types


def update_wrapper(wrapper, wrapped):
    func_code = wrapped.__code__
    inner_code = wrapper.__code__

    wrapped_code = types.CodeType(inner_code.co_argcount, inner_code.co_kwonlyargcount, inner_code.co_nlocals,
                                  inner_code.co_stacksize, inner_code.co_flags, inner_code.co_code,
                                  inner_code.co_consts, inner_code.co_names, inner_code.co_varnames,
                                  func_code.co_filename, func_code.co_name, func_code.co_firstlineno,
                                  func_code.co_lnotab, inner_code.co_freevars, inner_code.co_cellvars)
    res = types.FunctionType(wrapped_code, wrapper.__globals__, wrapped.__name__, wrapper.__defaults__,
                             wrapper.__closure__)
    res.__kwdefaults__ = wrapped.__kwdefaults__
    res.__annotations__ = wrapped.__annotations__
    res.__dict__ = wrapped.__dict__
    res.__qualname__ = wrapped.__qualname__
    res.__doc__ = wrapped.__doc__
    res.__module__ = wrapped.__module__

    return res


def to_exception(exc_type, exc_value=None, exc_tb=None):
    if exc_type is None:
        return None

    if isinstance(exc_type, BaseException):
        exc_value = exc_type
        exc_type = type(exc_value)

    if exc_value is None:
        exc_value = exc_type()

    if exc_tb is not None:
        exc_value = exc_value.with_traceback(exc_tb)

    return exc_value


__all__ = ['update_wrapper', 'to_exception']
