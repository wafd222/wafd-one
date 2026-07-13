app_name = "wafd_one"
app_title = "WAFD ONE"
app_publisher = "Wafd Almadinah"
app_description = "Integrated catering operations, projects, production, quality, fleet, delivery and finance management"
app_email = "wafd.almadinah@gmail.com"
app_license = "proprietary"
app_logo_url = "/assets/wafd_one/images/wafd-one-logo.svg"
app_color = "#B38A3E"

# Frappe v16 uses this hook to display custom apps on the Desktop/App switcher.
add_to_apps_screen = [
    {
        "name": "wafd_one",
        "logo": "/assets/wafd_one/images/wafd-one-logo.svg",
        "title": "WAFD ONE",
        "route": "/desk/wafd-one",
    }
]

after_install = "wafd_one.setup.after_install"
after_migrate = "wafd_one.setup.after_migrate"
