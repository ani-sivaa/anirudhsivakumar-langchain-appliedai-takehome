import unittest
from calculator import Calculator

class TestCalculator(unittest.TestCase):

    def setUp(self):
        self.calculator = Calculator()

    def test_addition(self):
        result = self.calculator.add(2, 3)
        self.assertEqual(result, 5)
        result = self.calculator.add(-1, 1)
        self.assertEqual(result, 0)
        result = self.calculator.add(-1, -1)
        self.assertEqual(result, -2)

    def test_subtraction(self):
        result = self.calculator.subtract(5, 3)
        self.assertEqual(result, 2)
        result = self.calculator.subtract(2, 3)
        self.assertEqual(result, -1)
        result = self.calculator.subtract(-1, -1)
        self.assertEqual(result, 0)

    def test_multiplication(self):
        result = self.calculator.multiply(2, 3)
        self.assertEqual(result, 6)
        result = self.calculator.multiply(-1, 1)
        self.assertEqual(result, -1)
        result = self.calculator.multiply(-1, -1)
        self.assertEqual(result, 1)

    def test_division(self):
        result = self.calculator.divide(6, 3)
        self.assertEqual(result, 2)
        result = self.calculator.divide(-6, 3)
        self.assertEqual(result, -2)
        result = self.calculator.divide(-6, -3)
        self.assertEqual(result, 2)
        with self.assertRaises(ZeroDivisionError):
            self.calculator.divide(1, 0)

    def test_division_by_zero(self):
        with self.assertRaises(ZeroDivisionError):
            self.calculator.divide(10, 0)

    def test_power(self):
        result = self.calculator.power(2, 3)
        self.assertEqual(result, 8)
        result = self.calculator.power(5, 0)
        self.assertEqual(result, 1)
        result = self.calculator.power(0, 5)
        self.assertEqual(result, 0)

    def test_square_root(self):
        result = self.calculator.square_root(9)
        self.assertEqual(result, 3)
        result = self.calculator.square_root(0)
        self.assertEqual(result, 0)
        with self.assertRaises(ValueError):
            self.calculator.square_root(-1)

if __name__ == '__main__':
    unittest.main()