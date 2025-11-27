print("WSGI starting...")

from app import create_app

print("Calling create_app()...")
app = create_app()
print("create_app() succeeded.")

if __name__ == "__main__":
    # Force Flask dev server to run
    app.run(host="127.0.0.1", port=5000, debug=True)

