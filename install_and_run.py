def main():
    from flask_app import install_web_app
    install_web_app.main()

    import start_app
    start_app.main()


if __name__ == "__main__":
    main()
