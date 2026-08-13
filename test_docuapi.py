import docuware

# Set server details
SERVER_URL = "https://doc.warden.com/docuware"
USERNAME = "awu"
PASSWORD = "2026March!"

# try:
#     dw = docuware.connect(
#         url=SERVER_URL,
#         username=USERNAME,
#         password=PASSWORD
#     )

#     print("Success")

#     for org in dw.organizations:
#         print(f"Organization: {org.name}")
#         for basket in org.baskets:
#             print(f" - Tray Name: {basket.name} | ID: {basket.id}")

# except Exception as e:
#     print("Connection failed: {e}")

dw = docuware.connect(
        url=SERVER_URL,
        username=USERNAME,
        password=PASSWORD
    )