from collections import UserDict
from datetime import datetime, timedelta
import pickle



def input_error(func):
    """Decorator for handling errors in command functions."""
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return "Contact not found."
        except ValueError as e:
            return str(e)
        except IndexError:
            return "Missing arguments. Please check the command format."
        except AttributeError:
            return "Contact not found or has no required attribute."
        except Exception as e:
            return f"Error: {str(e)}"
    return inner



class Field:
    def __init__(self, value):
        self.value = value


    def __str__(self):
        return str(self.value)



class Name(Field):
    def __init__(self, value):
        if not value or not value.strip():
            raise ValueError("Name cannot be empty")
        super().__init__(value)



class Phone(Field):
    def __init__(self, value):
        if not value.isdigit():
            raise ValueError("Phone number must contain only digits")
        if len(value) != 10:
            raise ValueError("Phone number must be exactly 10 digits")
        super().__init__(value)



class Birthday(Field):
    def __init__(self, value):
        try:
            birthday_date = datetime.strptime(value, "%d.%m.%Y")
            super().__init__(birthday_date)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")



class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None


    def add_phone(self, phone):
        """Add a phone number to the record."""
        phone_obj = Phone(phone)
        self.phones.append(phone_obj)


    def remove_phone(self, phone):
        """Remove a phone number from the record."""
        phone_obj = self.find_phone(phone)
        if phone_obj:
            self.phones.remove(phone_obj)
        else:
            raise ValueError(f"Phone {phone} not found")


    def edit_phone(self, old_phone, new_phone):
        """Edit an existing phone number."""
        phone_obj = self.find_phone(old_phone)
        if not phone_obj:
            raise ValueError(f"Phone {old_phone} not found")
        new_phone_obj = Phone(new_phone)
        index = self.phones.index(phone_obj)
        self.phones[index] = new_phone_obj


    def find_phone(self, phone):
        """Find a phone number in the record."""
        for p in self.phones:
            if p.value == phone:
                return p
        return None


    def add_birthday(self, birthday):
        """Add birthday to the contact."""
        self.birthday = Birthday(birthday)


    def __str__(self):
        phones_str = ('; '.join(p.value for p in self.phones)
                      if self.phones else "no phones")
        birthday_str = (f", birthday: "
                        f"{self.birthday.value.strftime('%d.%m.%Y')}"
                        if self.birthday else "")
        return (f"Contact name: {self.name.value}, "
                f"phones: {phones_str}{birthday_str}")



class AddressBook(UserDict):
    def add_record(self, record):
        """Add a record to the address book."""
        self.data[record.name.value] = record


    def find(self, name):
        """Find a record by name."""
        return self.data.get(name)


    def delete(self, name):
        """Delete a record by name."""
        if name in self.data:
            del self.data[name]
        else:
            raise KeyError(name)


    def get_upcoming_birthdays(self, days=7):
        """
        Returns a list of users whose birthdays are within the
        next 'days' days. If birthday falls on weekend,
        congratulation date is moved to next Monday.
        For Feb 29 birthdays in non-leap years, use Feb 28.
        """
        today = datetime.today().date()
        upcoming_birthdays = []


        for record in self.data.values():
            if not record.birthday:
                continue


            birthday_date = record.birthday.value.date()
            
            # Handle February 29 birthdays in non-leap years
            try:
                birthday_this_year = birthday_date.replace(year=today.year)
            except ValueError:
                # Feb 29 birthday in a non-leap year -> use Feb 28
                birthday_this_year = birthday_date.replace(year=today.year, day=28)


            if birthday_this_year < today:
                try:
                    birthday_this_year = birthday_date.replace(
                        year=today.year + 1)
                except ValueError:
                    # Feb 29 birthday in a non-leap year -> use Feb 28
                    birthday_this_year = birthday_date.replace(
                        year=today.year + 1, day=28)


            days_until_birthday = (birthday_this_year - today).days


            if 0 <= days_until_birthday <= days:
                congratulation_date = birthday_this_year
                weekday = congratulation_date.weekday()
                if weekday == 5:  # Saturday
                    congratulation_date += timedelta(days=2)
                elif weekday == 6:  # Sunday
                    congratulation_date += timedelta(days=1)


                upcoming_birthdays.append({
                    "name": record.name.value,
                    "birthday": birthday_this_year.strftime("%d.%m.%Y"),
                    "congratulation_date":
                        congratulation_date.strftime("%d.%m.%Y")
                })


        return upcoming_birthdays



def save_data(book, filename="addressbook.pkl"):
    """Save address book to file using pickle."""
    with open(filename, "wb") as f:
        pickle.dump(book, f)



def load_data(filename="addressbook.pkl"):
    """Load address book from file using pickle."""
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()  # Return new address book if file not found



def parse_input(user_input):
    """Parse user input into command and arguments."""
    if not user_input or not user_input.strip():
        return "", []
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, args



@input_error
def add_contact(args, book):
    """Add a new contact or add phone to existing contact."""
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message



@input_error
def change_contact(args, book):
    """Change the phone number of an existing contact."""
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    record.edit_phone(old_phone, new_phone)
    return "Contact updated."



@input_error
def show_phone(args, book):
    """Show phone numbers for a contact."""
    name, *_ = args
    record = book.find(name)
    if not record.phones:
        return "No phones for this contact."
    phones_str = '; '.join(p.value for p in record.phones)
    return f"Phone numbers for {record.name.value}: {phones_str}"



@input_error
def show_all(book):
    """Show all contacts in the address book."""
    if not book.data:
        return "No contacts in address book."
    result = []
    for name in sorted(book.data.keys()):
        result.append(str(book.data[name]))
    return "\n".join(result)



@input_error
def add_birthday(args, book):
    """Add birthday to an existing contact."""
    name, birthday, *_ = args
    record = book.find(name)
    record.add_birthday(birthday)
    return "Birthday added."



@input_error
def show_birthday(args, book):
    """Show birthday for a contact."""
    name, *_ = args
    record = book.find(name)
    if record.birthday:
        return f"{record.birthday.value.strftime('%d.%m.%Y')}"


    return "No birthday set for this contact."



@input_error
def birthdays(args, book):
    """Show upcoming birthdays for the next week."""
    upcoming = book.get_upcoming_birthdays()


    if not upcoming:
        return "No upcoming birthdays."
    result = ["Upcoming birthdays:"]
    for entry in upcoming:
        result.append(
            f"{entry['name']}: {entry['birthday']} "
            f"(congratulate on {entry['congratulation_date']})")


    return "\n".join(result)



def main():
    book = load_data()
    print("Welcome to the assistant bot!")
    while True:
        user_input = input(
            "Enter a command (help to see available commands): ")
        command, args = parse_input(user_input)


        if command in ["close", "exit"]:
            save_data(book)
            print("Good bye!")
            break


        elif command == "hello":
            print("How can I help you?")


        elif command == "add":
            print(add_contact(args, book))


        elif command == "change":
            print(change_contact(args, book))


        elif command == "phone":
            print(show_phone(args, book))


        elif command == "all":
            print(show_all(book))


        elif command == "add-birthday":
            print(add_birthday(args, book))


        elif command == "show-birthday":
            print(show_birthday(args, book))


        elif command == "birthdays":
            print(birthdays(args, book))


        elif command == "help":
            print("\nAvailable commands:")
            print("  hello - Get a greeting")
            print("  add [name] [phone] - Add new contact or "
                  "add phone to existing contact")
            print("  change [name] [old_phone] [new_phone] - "
                  "Change phone number")
            print("  phone [name] - Show phone numbers for a contact")
            print("  all - Show all contacts")
            print("  add-birthday [name] [DD.MM.YYYY] - "
                  "Add birthday to contact")
            print("  show-birthday [name] - Show birthday for a contact")
            print("  birthdays - Show upcoming birthdays in the next week")
            print("  close or exit - Exit the program")


        else:
            print("Invalid command.")



if __name__ == "__main__":
    main()
