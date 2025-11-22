import re

def validate_number_input(input_str):
    """
    Validates if the input string is a valid number (integer or float).
    
    Parameters:
    input_str (str): The input string to validate.
    
    Returns:
    bool: True if the input is a valid number, False otherwise.
    """
    # Regular expression to match a valid integer or float
    number_regex = r'^-?\d+(\.\d+)?$'
    return bool(re.match(number_regex, input_str))

def handle_division_by_zero(numerator, denominator):
    """
    Safely handles division, raising an error if division by zero is attempted.
    
    Parameters:
    numerator (float): The numerator of the division.
    denominator (float): The denominator of the division.
    
    Returns:
    float: The result of the division if valid.
    
    Raises:
    ZeroDivisionError: If the denominator is zero.
    """
    if denominator == 0:
        raise ZeroDivisionError("Cannot divide by zero.")
    return numerator / denominator

def parse_input(input_str):
    """
    Parses the input string to a float if it's a valid number.
    
    Parameters:
    input_str (str): The input string to parse.
    
    Returns:
    float: The parsed float number.
    
    Raises:
    ValueError: If the input is not a valid number.
    """
    if not validate_number_input(input_str):
        raise ValueError(f"Invalid number input: {input_str}")
    return float(input_str)

def safe_operation(operation_func, *args):
    """
    Safely executes a calculator operation, handling any exceptions.
    
    Parameters:
    operation_func (callable): The calculator operation function to execute.
    *args: Arguments to pass to the operation function.
    
    Returns:
    tuple: A tuple containing a boolean indicating success, and the result or error message.
    """
    try:
        result = operation_func(*args)
        return True, result
    except Exception as e:
        return False, str(e)