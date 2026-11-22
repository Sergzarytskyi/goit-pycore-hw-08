from collections import UserDict
from datetime import datetime, timedelta
import pickle
from pathlib import Path


FILE_PATH = Path(__file__).parent / "addressbook.pkl"

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        if not isinstance(value, str):
            raise ValueError("Phone must be a string.")
        if not value.isdigit():
            raise ValueError("Phone must contain only digits.")
        if len(value) != 10:
            raise ValueError("Phone must be 10 digits.")
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value):
        try:
            parsed_date = datetime.strptime(value, "%d.%m.%Y").date()
            super().__init__(parsed_date)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

    def __str__(self):
        return self.value.strftime("%d.%m.%Y")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        phone_object = self.find_phone(phone)
        if phone_object:
            raise ValueError(f"Phone {phone} already exists.")
        self.phones.append(Phone(phone))

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def remove_phone(self, phone):
        phone_object = self.find_phone(phone)
        if phone_object is None:
            raise ValueError(f"Phone {phone} not found.")
        self.phones.remove(phone_object)

    def edit_phone(self, old_phone, new_phone):
        phone_object = self.find_phone(old_phone)
        if phone_object is None:
            raise ValueError(f"Phone {old_phone} not found.")
        phone_object_new = self.find_phone(new_phone)
        if phone_object_new:
            raise ValueError(f"Phone {new_phone} already exists.")
        phone_index = self.phones.index(phone_object)
        self.phones[phone_index] = Phone(new_phone)

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        phones = "; ".join(p.value for p in self.phones)
        result =  f"Contact name: {self.name.value}, phones: {phones}"
        if self.birthday is not None:
            result += f", birthday: {self.birthday}"
        return result


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        return self.data.pop(name)

    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        upcoming_birthdays = []

        for record in self.data.values():
            if record.birthday is None:
                continue

            birthday = record.birthday.value

            try:
                birthday_this_year = birthday.replace(year=today.year)
            except ValueError:
                birthday_this_year = birthday.replace(year=today.year, day=28)

            if birthday_this_year < today:
                next_year = today.year + 1
                try:
                    birthday_this_year = birthday.replace(year=next_year)
                except ValueError:
                    birthday_this_year = birthday.replace(year=next_year,
                                                          day=28)

            days_until_birthday = (birthday_this_year - today).days

            if days_until_birthday <= 7:
                congratulation_date = birthday_this_year

                if congratulation_date.weekday() == 5:
                    congratulation_date += timedelta(days=2)
                elif congratulation_date.weekday() == 6:
                    congratulation_date += timedelta(days=1)

                upcoming_birthdays.append({
                    "name": record.name.value,
                    "congratulation_date":
                        congratulation_date.strftime("%d.%m.%Y")
                })

        return upcoming_birthdays

def save_data(book, filename=FILE_PATH):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename=FILE_PATH):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()  
    
def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return str(e)
        except IndexError:
            return "Enter user name."
        except KeyError:
            return "Contact not found."

    return inner

def parse_input(user_input):
    if not user_input.strip():
        cmd = ""
        return cmd,
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args

@input_error
def add_contact(args, book: AddressBook):
    if len(args) < 2:
        raise ValueError("Give me name and phone please.")
    name, phone, *_ = args
    name = name.capitalize()
    record = book.find(name)
    if record is None:
        record = Record(name)
        record.add_phone(phone)
        book.add_record(record)
        return "Contact added."
    record.add_phone(phone)
    return "Contact updated."

@input_error
def change_contact(args, book: AddressBook):
    if len(args) < 3:
        raise ValueError("Give me name, old phone and new phone please.")
    name, old_phone, new_phone, *_ = args
    name = name.capitalize()
    record = book.find(name)
    if record is None:
        raise KeyError(name)
    
    record.edit_phone(old_phone, new_phone)
    return "Phone updated."

@input_error
def show_phone(args, book: AddressBook):
    name = args[0]
    name = name.capitalize()
    record = book.find(name)
    if record is None:
        raise KeyError(name)
    
    if not record.phones:
        return "No phones."
    else:
        return "; ".join(p.value for p in record.phones)

@input_error
def show_all(book: AddressBook):
    if not book.data:
        return "Contacts list is empty."
    
    result = [str(record) for record in book.data.values()]
    return "\n".join(result)

@input_error
def add_birthday(args, book: AddressBook):
    if len(args) < 2:
        raise ValueError("Give me name and birthday please.")
    name, birthday, *_ = args
    name = name.capitalize()
    record = book.find(name)
    if record is None:
        raise KeyError(name)
    
    record.add_birthday(birthday)
    return "Birthday added."

@input_error
def show_birthday(args, book: AddressBook):
    name = args[0]
    name = name.capitalize()
    record = book.find(name)
    if record is None:
        raise KeyError(name)
        
    if record.birthday is None:
        return "No birthday."
    else:
        return str(record.birthday)

@input_error
def birthdays(args, book: AddressBook):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No upcoming birthdays."
    
    result = [f"{item['name']}: {item['congratulation_date']}" for item in upcoming]
    return "\n".join(result)

def main():
    book = load_data()
    print("Welcome to the assistant bot!")
    while True:
        try:
            user_input = input("Enter a command: ")
        except (KeyboardInterrupt, EOFError):
            save_data(book)
            print("\nGood bye!")
            break

        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            save_data(book)
            break
        elif command == "":
            print("Command is empty. Please try again.")
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
        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()
