print("WSGI starting...")

from app import create_app

print("Calling create_app()...")

try:
    app = create_app()
    print("create_app() succeeded.")
except Exception as e:
    print("Error inside create_app():", e)
    raise e

if __name__ == "__main__":
    app.run(debug=True)

