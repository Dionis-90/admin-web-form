# SMTP service settings
USE_SMTP = False  # If False - trying to send emails via unix sendmail script if exists.
SMTP_SERVER = ''
SMTP_USER = ''
SMTP_PASSWORD = ''
SMTP_USE_SSL = True
SMTP_PORT = 465  # Supported only 465 port now. TODO: sent via 587 and 25 with starttls or without.

# Email settings
SENDER_ADDRESS = 'webform@localhost.localdomain'
SENDER_NAME = 'Admin Web Form'
SUBJECT = 'Form submitted.'
ADMIN_EMAIL = 'admin@example.com'  # Who will receive emails form this form.

# Absolute or relative paths.
SCREENSHOTS_DIR = 'screenshots/'  # With '/' on the end!
PATH_TO_DB = 'db.sqlite'
PATH_TO_APP_CONFIG = 'form.conf'
