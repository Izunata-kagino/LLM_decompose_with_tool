"""
Calculator tool for mathematical computations
"""
from typing import Dict, Any, Optional
import ast
import operator
import math
import re

from ..base import BaseTool, ToolResult, ToolExecutionContext, ToolCategory


class CalculatorTool(BaseTool):
    """
    Calculator tool for evaluating mathematical expressions safely

    Supports:
    - Basic arithmetic: +, -, *, /, //, %, **
    - Math functions: sin, cos, tan, sqrt, log, exp, etc.
    - Constants: pi, e
    """

    # Safe operators
    SAFE_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    # Safe functions
    SAFE_FUNCTIONS = {
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
        'sum': sum,
        # Math functions
        'sqrt': math.sqrt,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'asin': math.asin,
        'acos': math.acos,
        'atan': math.atan,
        'sinh': math.sinh,
        'cosh': math.cosh,
        'tanh': math.tanh,
        'log': math.log,
        'log10': math.log10,
        'log2': math.log2,
        'exp': math.exp,
        'pow': pow,
        'ceil': math.ceil,
        'floor': math.floor,
        'factorial': math.factorial,
        'gcd': math.gcd,
        'degrees': math.degrees,
        'radians': math.radians,
    }

    # Safe constants
    SAFE_CONSTANTS = {
        'pi': math.pi,
        'e': math.e,
        'tau': math.tau,
        'inf': math.inf,
    }

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return (
            "计算数学表达式。支持基本算术运算、三角函数、对数函数等。"
            "示例: '2 + 2', 'sqrt(16)', 'sin(pi/2)', 'log(100, 10)'"
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "要计算的数学表达式，例如：'2 + 2', 'sqrt(16)', 'sin(pi/2)'"
                }
            },
            "required": ["expression"]
        }

    async def execute(
        self,
        arguments: Dict[str, Any],
        context: Optional[ToolExecutionContext] = None
    ) -> ToolResult:
        """Execute calculator"""
        expression = arguments.get("expression", "").strip()

        if not expression:
            return ToolResult.error_result("表达式不能为空")

        try:
            # Evaluate expression safely
            result = await self._run_sync(self._safe_eval, expression)

            return ToolResult.success_result(
                output=result,
                metadata={
                    "expression": expression,
                    "result_type": type(result).__name__
                }
            )

        except SyntaxError as e:
            return ToolResult.error_result(f"语法错误: {str(e)}")
        except ValueError as e:
            return ToolResult.error_result(f"值错误: {str(e)}")
        except ZeroDivisionError:
            return ToolResult.error_result("除零错误")
        except Exception as e:
            return ToolResult.error_result(f"计算错误: {str(e)}")

    def _safe_eval(self, expression: str) -> float:
        """
        Safely evaluate a mathematical expression

        Args:
            expression: Mathematical expression to evaluate

        Returns:
            Result of the evaluation

        Raises:
            ValueError: If expression contains unsafe operations
            SyntaxError: If expression has syntax errors
        """
        # Parse the expression
        try:
            node = ast.parse(expression, mode='eval')
        except SyntaxError as e:
            raise SyntaxError(f"无法解析表达式: {str(e)}")

        # Evaluate the AST
        return self._eval_node(node.body)

    def _eval_node(self, node):
        """Recursively evaluate AST node"""
        if isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        elif isinstance(node, ast.Num):  # Python 3.7
            return node.n
        elif isinstance(node, ast.Name):
            # Check if it's a safe constant
            if node.id in self.SAFE_CONSTANTS:
                return self.SAFE_CONSTANTS[node.id]
            else:
                raise ValueError(f"未知的常量: {node.id}")
        elif isinstance(node, ast.BinOp):
            # Binary operation
            op_type = type(node.op)
            if op_type not in self.SAFE_OPERATORS:
                raise ValueError(f"不支持的操作: {op_type.__name__}")

            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return self.SAFE_OPERATORS[op_type](left, right)
        elif isinstance(node, ast.UnaryOp):
            # Unary operation
            op_type = type(node.op)
            if op_type not in self.SAFE_OPERATORS:
                raise ValueError(f"不支持的操作: {op_type.__name__}")

            operand = self._eval_node(node.operand)
            return self.SAFE_OPERATORS[op_type](operand)
        elif isinstance(node, ast.Call):
            # Function call
            if not isinstance(node.func, ast.Name):
                raise ValueError("不支持的函数调用")

            func_name = node.func.id
            if func_name not in self.SAFE_FUNCTIONS:
                raise ValueError(f"未知的函数: {func_name}")

            # Evaluate arguments
            args = [self._eval_node(arg) for arg in node.args]

            # Call function
            return self.SAFE_FUNCTIONS[func_name](*args)
        elif isinstance(node, ast.List):
            # List literal
            return [self._eval_node(elt) for elt in node.elts]
        elif isinstance(node, ast.Tuple):
            # Tuple literal
            return tuple(self._eval_node(elt) for elt in node.elts)
        else:
            raise ValueError(f"不支持的表达式类型: {type(node).__name__}")
