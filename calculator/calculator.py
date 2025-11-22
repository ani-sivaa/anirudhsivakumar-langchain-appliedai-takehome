class Calculator:
    def add(self, a, b):
        """Return the sum of two numbers."""
        return a + b

    def subtract(self, a, b):
        """Return the difference of two numbers."""
        return a - b

    def multiply(self, a, b):
        """Return the product of two numbers."""
        return a * b

    def divide(self, a, b):
        """Return the division of two numbers. Raises ValueError on division by zero."""
        if b == 0:
            raise ValueError("Cannot divide by zero.")
        return a / b

if __name__ == "__main__":
    calc = Calculator()
    print("Addition: 5 + 3 =", calc.add(5, 3))
    print("Subtraction: 5 - 3 =", calc.subtract(5, 3))
    print("Multiplication: 5 * 3 =", calc.multiply(5, 3))
    print("Division: 5 / 3 =", calc.divide(5, 3))