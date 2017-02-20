# Changelog
## v1.0.0
- Not any longer subclasses `flask.Flask`. This was ugly, and bad.
    - renamed `TeleflaskComplete` to just `Teleflask`
    
    Now you initialize it like this:
    ```python
    bot = Teleflask(API_KEY, app)
    ```
    or 
    ```python
    bot = Teleflask(API_KEY)
    bot.init_app(app)
    ```
        
