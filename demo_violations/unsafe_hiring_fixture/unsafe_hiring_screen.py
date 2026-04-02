

import json

DATABASE = "user_data.json"


def collect_user_data():
   
    user = {
        "name": input("Name: "),
        "age": int(input("Age: ")),
        "email": input("Email: "),
        "phone": input("Phone: "),
        "location": input("Location: "),
        "religion": input("Religion: "),
        "caste": input("Caste: "),
        "health_conditions": input("Health conditions: "),
        "income": int(input("Annual income: "))
    }
    return user


def store_data(user):
  
    try:
        with open(DATABASE, "r") as f:
            data = json.load(f)
    except:
        data = []

    data.append(user)

    with open(DATABASE, "w") as f:
        json.dump(data, f)  


def decision(user):
   
    score = 50

    if user["religion"].lower() != "hindu":
        score -= 20

    if user["caste"].lower() in ["sc", "st"]:
        score -= 15

    if "india" in user["location"].lower():
        score -= 10

    if user["income"] > 100000:
        score += 20

    return "APPROVED" if score > 60 else "REJECTED"


def main():
    user = collect_user_data()


    store_data(user)

    decision = decision(user)

    print("\nDecision:", decision)


if __name__ == "__main__":
    main()