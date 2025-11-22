import sys

def add(x, y):
    return x + y

def subtract(x, y):
    return x - y

def multiply(x, y):
    return x * y

def divide(x, y):
    if y == 0:
        raise ValueError("Cannot divide by zero.")
    return x / y

def get_operation():
    print("Select operation:")
    print("1. Add")
    print("2. Subtract")
    print("3. Multiply")
    print("4. Divide")
    
    while True:
        choice = input("Enter choice(1/2/3/4): ")
        if choice in ['1', '2', '3', '4']:
            return choice
        else:
            print("Invalid input. Please enter a number between 1 and 4.")

def get_numbers():
    while True:
        try:
            num1 = float(input("Enter first number: "))
            num2 = float(input("Enter second number: "))
            return num1, num2
        except ValueError:
            print("Invalid input. Please enter numeric values.")

def main():
    while True:
        operation = get_operation()
        num1, num2 = get_numbers()

        try:
            if operation == '1':
                result = add(num1, num2)
                print(f"The result of {num1} + {num2} is {result}")
            elif operation == '2':
                result = subtract(num1, num2)
                print(f"The result of {num1} - {num2} is {result}")
            elif operation == '3':
                result = multiply(num1, num2)
                print(f"The result of {num1} * {num2} is {result}")
            elif operation == '4':
                result = divide(num1, num2)
                print(f"The result of {num1} / {num2} is {result}")
        except ValueError as e:
            print(e)

        next_calculation = input("Do you want to perform another calculation? (yes/no): ")
        if next_calculation.lower() != 'yes':
            print("Exiting the calculator. Goodbye!")
            break

if __name__ == "__main__":
    main()