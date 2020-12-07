f"""From: Admin Web Form <{SENDER_ADDRESS}>
To: <{ADMIN_EMAIL}>
Subject: Form Submitted
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary={EMAIL_MARKER}

--{EMAIL_MARKER}
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: 8bit

Name: {self.name}
Email: {self.email}
Ran command: {self.ran_commands}
Produced output: {self.produced_output}
Expected: {self.expected}
OS: {self.os_type}
Has root access: {self.has_root}

--{EMAIL_MARKER}
Content-Type: {self.screenshot.content_type}; name=\"{self.new_filename}\"
Content-Transfer-Encoding: base64
Content-Disposition: attachment; filename={self.new_filename}

{encoded_content.decode('ascii')}
--{EMAIL_MARKER}--
"""