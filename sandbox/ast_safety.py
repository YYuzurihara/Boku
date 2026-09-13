"""Static AST-based safety checker for candidate ``solve(xs, k)`` code.

This is a *defense-in-depth* layer, not the primary isolation mechanism.
Real isolation comes from running untrusted code inside a locked-down
Docker container (see ``Dockerfile`` / ``runner.py`` / ``client.py``): no
network, dropped capabilities, a read-only root filesystem, a non-root
user, and OS-enforced CPU/memory/pid limits. This module exists to reject
obviously dangerous or out-of-scope code *before* a container is even
started (cheap host-side pre-check), and again inside the container as a
second line of defense right before ``exec()``.

Design note on attribute access
--------------------------------
homework.md's screening rule says generated code must not contain
"import, attribute access, file operations, etc." (`import、属性アクセス、
ファイル操作などを含まない`). Taken completely literally this would also
forbid the plain ``for`` loop + ``result.append(x)`` style that
homework.md separately requires as a structural code variation
(`内包表記と通常のforループ`). We resolve the tension by allowing a small
fixed allowlist of safe list-mutation methods and rejecting every other
attribute access -- in particular anything starting with ``_`` (which
blocks classic sandbox-escape chains such as ``().__class__.__bases__``)
and any access into a module object (moot anyway, since ``import`` is
banned outright so no module object can exist).
"""

from __future__ import annotations

import ast

REQUIRED_FUNCTION_NAME = "solve"
REQUIRED_PARAMS = ("xs", "k")

# list methods needed for normal (non-comprehension) solve() implementations.
SAFE_ATTR_METHODS = {
    "append", "extend", "insert", "remove", "pop", "clear",
    "sort", "reverse", "count", "index", "copy",
}

# builtins the narrow xs/k-list domain plausibly needs. Anything else
# (open, eval, exec, compile, __import__, input, globals, locals, vars,
# dir, getattr, setattr, print, ...) is rejected by omission.
ALLOWED_CALL_NAMES = {
    "len", "range", "sorted", "sum", "min", "max", "abs", "all", "any",
    "list", "set", "tuple", "dict", "int", "float", "bool", "round",
    "divmod", "pow", "enumerate", "zip", "map", "filter", "reversed",
}

# Everything not in this tuple is rejected. Notably absent: Import,
# ImportFrom, ClassDef, (Async)FunctionDef nested anywhere but the top
# level, With, Try, Raise, Assert, Delete, Global, Nonlocal, Yield,
# YieldFrom, Await -- i.e. exactly the "対象外の要素" in homework.md.
ALLOWED_NODES = (
    ast.Module,
    ast.FunctionDef, ast.arguments, ast.arg,
    ast.Return, ast.Pass, ast.Break, ast.Continue,
    ast.If, ast.For, ast.While,
    ast.Assign, ast.AugAssign, ast.AnnAssign,
    ast.Expr,
    ast.Load, ast.Store,
    ast.Constant,
    ast.List, ast.Tuple, ast.Set, ast.Dict,
    ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp, ast.comprehension,
    ast.Lambda,
    ast.IfExp,
    ast.Subscript, ast.Slice,
    ast.Call, ast.keyword, ast.Starred,
    ast.Attribute,
    ast.BoolOp, ast.BinOp, ast.UnaryOp, ast.Compare,
    ast.And, ast.Or, ast.Not, ast.UAdd, ast.USub, ast.Invert,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.Is, ast.IsNot, ast.In, ast.NotIn,
    ast.Name,
)


class UnsafeCodeError(ValueError):
    """Raised when candidate code fails the static safety/signature check."""


def check_syntax(code: str) -> ast.Module:
    """Parse ``code``. Raises SyntaxError (propagated from ast.parse) if invalid."""
    return ast.parse(code, mode="exec")


def check_safety(tree: ast.Module) -> None:
    """Raise UnsafeCodeError if ``tree`` contains anything outside the
    narrow allowlist for this task's ``solve(xs, k)`` domain."""
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_NODES):
            lineno = getattr(node, "lineno", "?")
            raise UnsafeCodeError(f"disallowed syntax: {type(node).__name__} at line {lineno}")

        if isinstance(node, ast.Name) and node.id.startswith("__"):
            raise UnsafeCodeError(f"disallowed dunder name: {node.id}")

        if isinstance(node, ast.Attribute):
            if node.attr.startswith("_") or node.attr not in SAFE_ATTR_METHODS:
                raise UnsafeCodeError(f"disallowed attribute access: .{node.attr}")

        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                if func.id == REQUIRED_FUNCTION_NAME:
                    raise UnsafeCodeError("recursive call to solve() is not allowed")
                if func.id not in ALLOWED_CALL_NAMES:
                    raise UnsafeCodeError(f"disallowed function call: {func.id}(...)")
            elif isinstance(func, (ast.Attribute, ast.Lambda)):
                pass  # validated separately (Attribute above) or harmless (Lambda)
            else:
                raise UnsafeCodeError("disallowed call target")


def check_signature(tree: ast.Module) -> None:
    """Raise UnsafeCodeError unless ``tree`` is exactly one top-level
    function named ``solve(xs, k)`` and nothing else at module scope."""
    top_level_defs = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    if len(top_level_defs) != 1:
        raise UnsafeCodeError("expected exactly one top-level function definition")

    fn = top_level_defs[0]
    if fn.name != REQUIRED_FUNCTION_NAME:
        raise UnsafeCodeError(f"top-level function must be named '{REQUIRED_FUNCTION_NAME}'")
    if fn.decorator_list:
        raise UnsafeCodeError("decorators are not allowed")

    args = fn.args
    if args.vararg or args.kwarg or args.kwonlyargs or args.posonlyargs or args.defaults:
        raise UnsafeCodeError("solve() must take exactly (xs, k) with no extra/default args")

    param_names = tuple(a.arg for a in args.args)
    if param_names != REQUIRED_PARAMS:
        raise UnsafeCodeError(f"solve() parameters must be {REQUIRED_PARAMS}, got {param_names}")

    other_top_level = [n for n in tree.body if n is not fn]
    if other_top_level:
        raise UnsafeCodeError("no statements are allowed outside of solve()")

    for node in ast.walk(fn):
        if node is fn:
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            raise UnsafeCodeError("nested function/class definitions are not allowed")


def verify_static(code: str) -> ast.Module:
    """Run the full static verification pipeline (syntax, safety,
    signature). Returns the parsed tree on success; raises SyntaxError or
    UnsafeCodeError otherwise."""
    tree = check_syntax(code)
    check_safety(tree)
    check_signature(tree)
    return tree
