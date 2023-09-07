"""
Sample Tests
"""
from django.test import SimpleTestCase
from app import calc

class CalcTests(SimpleTestCase):
    """Class to test calc module."""

    def test_add_numbers(self):
        """Test for adding two numbers."""
        res = calc.add(5, 6)

        self.assertEqual(res, 11)

    def test_subtract_numbers(self):
        """Test for subtracting two numbers."""
        res = calc.subtract(10, 15)

        self.assertEqual(res, 5)