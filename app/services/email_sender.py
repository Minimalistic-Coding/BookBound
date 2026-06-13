import os
# from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage


class Email:

    def __init__(self, from_user, to_contacts):
        self.email_obj = EmailMessage()
        self.from_user = from_user
        self.contacts_list = to_contacts

    @staticmethod
    def select_files(files=False, images=False, path=None, filename=None):
        import tkinter as tk
        from tkinter import filedialog

        if path:

            if filename:

                if (file_path := os.path.exists(os.path.join(path, filename))):

                    return file_path

                else:

                    print("File Doesn't Exits!")

            else:

                if os.path.exists(path):

                    return os.path.join("", path)

                else:

                    print("Path Doesn't Exists!")

        root = tk.Tk()
        root.withdraw()

        filetypes = None

        if images:
            image_extensions = (
                ".jpg", ".jpeg", ".png", ".gif", ".bmp",
                ".tiff", ".tif", ".webp", ".svg", ".ico"
            )

            # Join extensions like: "*.jpg;*.jpeg;*.png"
            image_filter = ";".join([f"*{ext}" for ext in image_extensions])

            # Correctly define filetypes as a list of tuples
            filetypes = [
                ("All Files", "*.*"),
                ("Gmail Supported Images", image_filter)
            ]

        elif files:
            extensions = (
            # Documents & Text
            ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".rtf", ".csv", ".odt", ".ods", ".odp",
            # Audio
            ".mp3", ".wav", ".aac", ".ogg", ".flac", ".m4a",
            # Video
            ".mp4", ".mov", ".avi", ".mkv", ".webm", ".wmv", ".flv",
            # Archives
            ".zip", ".rar", ".7z", ".tar", ".gz", ".json"
        )

            files_filter = ";".join([f"*{ext}" for ext in extensions])

            filetypes = [
                ("All Files", "*.*"),
                ("Gmail Supported Files", files_filter)
            ]

        files = filedialog.askopenfilenames(
            filetypes=filetypes
        )

        if not files:
            raise ValueError("[ERROR] No Files Selected")

        return files

    def basic_construct(self, subject, txt_content):
        vals = [subject, txt_content]

        for val in vals:
            if not isinstance(val, str):
                raise ValueError("[ERROR] Provided Information is Not in Correct Form(string)!")
            elif val == "":
                raise ValueError("[ERROR] Provided Information must not be empty!")

        try:
            self.email_obj["Subject"] = vals[0]
            self.email_obj["From"] = self.from_user
            self.email_obj["To"] = self.contacts_list
            self.email_obj.set_content(vals[1])
        except Exception as e:
            print(f"[ERROR] {e}")

    def add_html(self, html_str):
        if not isinstance(html_str, str):
            raise ValueError("[ERROR] Provided Information is Not in Correct Form(string)!")
        elif html_str == "":
            raise ValueError("[ERROR] Provided Information must not be empty!")

        self.email_obj.add_alternative(f"""
            {html_str}
            """, subtype="html")

    def add_attachment(self, images=False, files=False, path=None, filename=None):

        extensions = (
            # Documents & Text
            ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".rtf", ".csv", ".odt", ".ods", ".odp",
            # Audio
            ".mp3", ".wav", ".aac", ".ogg", ".flac", ".m4a",
            # Video
            ".mp4", ".mov", ".avi", ".mkv", ".webm", ".wmv", ".flv",
            # Archives
            ".zip", ".rar", ".7z", ".tar", ".gz", ".json"
        )

        if images:
            files = Email.select_files(images=True)

            for file in files:

                if os.path.getsize(file) > 25 * 1024 * 1024:
                    print(f"[ERROR] {os.path.basename(file)} exceeds Gmail's 25 MB limit!")
                    continue

                filepath, ext = os.path.splitext(file)

                if ext.lower() in (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp", ".svg", ".ico"):
                    file_data = b""
                    with open(file, "rb") as rf:
                        while chunk := rf.read(4096):
                            file_data += chunk

                    self.email_obj.add_attachment(
                        file_data,
                        maintype="image",
                        subtype=ext.strip("."),
                        filename=os.path.basename(file)
                    )

                else:
                    raise ValueError(f"[ERROR] {os.path.basename(file)} is not a supported file!")

        elif files:
            files = Email.select_files(files=True)

            for file in files:

                if os.path.getsize(file) > 25 * 1024 * 1024:
                    print(f"[ERROR] {os.path.basename(file)} exceeds Gmail's 25 MB limit!")
                    continue

                filepath, ext = os.path.splitext(file)

                if ext.lower() in extensions:
                    file_data = b""
                    with open(file, "rb") as rf:
                        while chunk := rf.read(4096):
                            file_data += chunk

                    self.email_obj.add_attachment(
                        file_data,
                        maintype="application",
                        subtype="octet-stream",
                        filename=os.path.basename(file)
                    )

                else:
                    raise ValueError(f"[ERROR] {os.path.basename(file)} is not a supported file!")

        elif path and filename:

            file = Email.select_files(path=path, filename=filename)

            if os.path.getsize(file) > 25 * 1024 * 1024:
                print(f"[ERROR] {os.path.basename(file)} exceeds Gmail's 25 MB limit!")
                return

            filepath, ext = os.path.splitext(file)

            if ext.lower() in extensions:
                file_data = b""
                with open(file, "rb") as rf:
                    while chunk := rf.read(4096):
                        file_data += chunk

                self.email_obj.add_attachment(
                    file_data,
                    maintype="application",
                    subtype="octet-stream",
                    filename=os.path.basename(file)
                )

            else:
                raise ValueError(f"[ERROR] {os.path.basename(file)} is not a supported file!")
                    
        print("Added Successfully!")

    def add_contacts(self, contacts):
        try:
            clean_contacts = []

            if contacts:
                for contact in contacts:
                    if not contact.endswith("@gmail.com"):
                        print(f"[ERROR] {contact} Not in Proper Format!")
                        continue
                    else:
                        clean_contacts.append(contact.strip())

                self.contacts_list = clean_contacts
            else:
                print("[ERROR] No Contacts Provided!")

        except Exception as e:
            print(f"[ERROR] {e}")


class Client:

    def __init__(self):
        load_dotenv()

        password = os.getenv("Email_Password")
        email = os.getenv("Email_Account")

        if password and email:
            self.__password = password
            self.__email_account = email
        else:
            raise FileNotFoundError("[ERROR] Wasn't Able to Access/Load ENV File for Account Information!")

    @property
    def email(self):
        return self.__email_account

    @property
    def password(self):
        return self.__password

    def send_email(self, Email_Message):
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(self.email, self.password)
                smtp.send_message(Email_Message.email_obj)
                print("Successfully Sent Email!")
        except Exception as e:
            print(f"[ERROR] {e}")

# email_msg = Email("joshuaimran0000@gmail.com", ["joshuaimran8989@gmail.com", "joshuaimran666@gmail.com"])
# email_msg.basic_construct("Hey, i sended one again with images", "I sended this email using a module i made, tell me how was it! this time i added images")
# email_msg.add_contacts(["joshuaimran8989@gmail.com", "joshuaimran666@gmail.com", "wassup,nigger"])
# # email_msg.add_attachment(images=True)
# email_msg.add_attachment(files=True)

# client = Client()
# client.send_email(email_msg)