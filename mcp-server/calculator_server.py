import math

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("calculator")


@mcp.tool()
def add(a: float, b: float) -> float:
    """두 수를 더합니다."""
    return a + b


@mcp.tool()
def subtract(a: float, b: float) -> float:
    """두 수를 뺍니다."""
    return a - b


@mcp.tool()
def multiply(a: float, b: float) -> float:
    """두 수를 곱합니다."""
    return a * b


@mcp.tool()
def divide(a: float, b: float) -> float:
    """두 수를 나눕니다. (b가 0이면 오류)"""
    if b == 0:
        raise ValueError("0으로 나눌 수 없습니다.")
    return a / b


@mcp.tool()
def power(base: float, exponent: float) -> float:
    """base의 exponent 제곱을 계산합니다."""
    return base ** exponent


@mcp.tool()
def sqrt(a: float) -> float:
    """제곱근을 계산합니다. (음수면 오류)"""
    if a < 0:
        raise ValueError("음수의 제곱근은 계산할 수 없습니다.")
    return math.sqrt(a)


@mcp.tool()
def modulo(a: float, b: float) -> float:
    """a를 b로 나눈 나머지를 계산합니다. (b가 0이면 오류)"""
    if b == 0:
        raise ValueError("0으로 나눌 수 없습니다.")
    return a % b


if __name__ == "__main__":
    mcp.run()
