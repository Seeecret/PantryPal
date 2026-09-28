from plyer import notification

notification.notify(
    title="PantryPal Test",
    message="🎉 Your PantryPal notifications are working!",
    app_name="PantryPal",
    timeout=10
)

input("Press Enter to close...")