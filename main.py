def main():
    print("Hello from agenticai!")

# Whenever Python runs a script, it automatically defines a special built-in variable called __name__
# If you run the file directly from the terminal (e.g., python main.py), 
#   Python assigns the value "__main__" to the __name__ variable.
#       In this case, if __name__ == "__main__": is True, and the main() function is executed.
# If you import the file as a module in another script (e.g., import main in another file), 
#   Python sets the value of __name__ to the actual filename (e.g., "main").
#       In this case, if __name__ == "__main__": is False, and the main() function is skipped.
# It allows your script to be both run as a standalone program and imported into other files as a 
#   module without executing the code inside main() immediately. It can safely access the helper functions inside a main.py
#   without accidentally triggering the portfolio tracking flow that resides inside track_momentum.py's main() block.
if __name__ == "__main__":
    main()
