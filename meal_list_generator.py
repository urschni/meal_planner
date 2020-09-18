import os.path
import sqlite3
import random
import logging

# Delete old database file
if os.path.exists("meals_database.db"):
    os.remove("meals_database.db")

# Create database file  and connector
con = sqlite3.connect("meals_database.db")
# Debug settings
logging.basicConfig(level=logging.DEBUG)
#con.set_trace_callback(print)
db = con.cursor()


def insert_into_meals(db, name, description=None, tags=[], lasts_for=1):
    tag_ids = []
    #print("tags:", tags)
    for tag in tags:
        #print("tag:", tag)
        db.execute("SELECT tag_id FROM tags WHERE name=?;", (tag,))
        select_output = db.fetchone()[0]
        #print("select output:", select_output)
        tag_ids.append(int(select_output))
    db.execute("INSERT INTO meals(name, description, lasts_for) VALUES(?, ?, ?);", (name, description, lasts_for))

    if tag_ids:
        db.execute("SELECT meal_id FROM meals WHERE name=?;", (name,))
        select_output = db.fetchone()[0]
        #print("select output:", select_output)
        meal_id = int(select_output)
        for tag_id in tag_ids:
            db.execute("INSERT INTO meals_tags(meal_id, tag_id) VALUES(?, ?);", (meal_id, tag_id))


def insert_into_tags(db, name, description=None, duration=1):
    db.execute("INSERT INTO tags(name, description, duration) VALUES(?, ?, ?);", (name, description, duration))


def get_random_meal_without_tags(db, tags):
    if isinstance(tags, int):
        tag_string = "(" + str(tags) + ")"
    elif isinstance(tags, (tuple, list)):
        if len(tags) > 1:
            tag_string = str(tuple(tags))
        elif len(tags) == 1:
            tag_string = "(" + str(tags[0]) + ")"
        else:
            tag_string = "()"
    query = "SELECT DISTINCT * FROM meals WHERE meals.meal_id NOT IN (SELECT DISTINCT meals_tags.meal_id from meals_tags WHERE meals_tags.tag_id IN {}) ORDER BY random() LIMIT 1;".format(tag_string)
    db.execute(query)
    return db.fetchall()[0]


def get_tag_id_from_name(db, name):
    db.execute("SELECT DISTINCT tag_id FROM tags WHERE name=?;", (name,))
    return db.fetchone()[0]


def get_tag_ids_to_meal_id(db, meal_id):
    db.execute("SELECT DISTINCT tag_id FROM meals_tags WHERE meal_id=?", (meal_id,))
    return db.fetchall()


def get_tag_by_id(db, tag_id):
    db.execute("SELECT DISTINCT * FROM tags WHERE tag_id=?;", (tag_id,))
    return db.fetchone()


## Create tables for meals and tags
# lasts_for -> How many days can you eat from this meal?
db.execute("""CREATE TABLE meals(
    meal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL, 
    description TEXT, 
    lasts_for INTEGER
    );""")
# duration -> minimum number of days between the use of this tag
db.execute("""CREATE TABLE tags(
    tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL, 
    description TEXT, 
    duration INTEGER
    );""")
db.execute("""
    CREATE TABLE meals_tags(
    meal_tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
    meal_id INTEGER,
    tag_id INTEGER,
    FOREIGN KEY(meal_id) REFERENCES meals(meal_id),
    FOREIGN KEY(tag_id) REFERENCES tags(tag_id)
    );""")
con.commit()

# Insert example values
example_tags = [("Nudeln", 1), ("Fleisch", 1), ("Aufwändig", 3), ("Kartoffeln", 1)]
for tag in example_tags:
    insert_into_tags(db, name=tag[0], duration=tag[1])
# Structure (name, [tag1, tag2, ...]),
example_meals = [("Spaghetti Bolognese", ["Nudeln", "Fleisch"]), ("Spaghetti Carbonara", ["Nudeln"]), ("Nudelauflauf", ["Nudeln", "Aufwändig"]), ("Ofenkartoffeln", ["Kartoffeln"])]
for meal in example_meals:
    insert_into_meals(db, name=meal[0], tags=meal[1], lasts_for=random.choice([1, 2, 3]))
con.commit()

# Test get_meals_without_tags
meals = get_random_meal_without_tags(db, (1, 2))
print("meals without Nudeln or Fleisch:", meals)

# Test get_tag_id_from_name
print("Nudeln id:", get_tag_id_from_name(db, "Nudeln"))

# Test get_tag_by_id
print("Tag with ID 3:", get_tag_by_id(db, 3))

# Create plan
number_of_days = 7
tags_not_allowed = [set() for a in range(number_of_days)]
meals = [None] * number_of_days

#all_meals = get_meals_without_tags(db, 0)

for current_day in range(number_of_days):
    print("Meals on day", current_day, ":", meals)
    print("tags not allowed on day", current_day, ":", tags_not_allowed)
    if meals[current_day] is not None:
        print("Skip day", current_day)
        continue
    # Get banned tags
    banned_tags = tags_not_allowed[current_day]
    # Get all possible meals
    selected_meal = get_random_meal_without_tags(db, tuple(banned_tags))
    # Select meal
    meal_id, meal_name, meal_description, meal_lasts_for = selected_meal
    meal_tag_ids = get_tag_ids_to_meal_id(db, meal_id)
    print("meal tag ids:", meal_tag_ids)

    for a in range(meal_lasts_for):
        if current_day + a < number_of_days:
            meals[current_day + a] = meal_name
        else:
            break
    for tag in meal_tag_ids:
        print("tag:", tag, "", type(tag))
        tag_info = get_tag_by_id(db, tag[0])
        print("Info to tag", tag[0], ":", tag_info)
        tag_id, tag_name, tag_description, tag_duration = tag_info
        print("tag duration: %s" % tag_duration)
        for a in range(tag_duration):
            pos = current_day + meal_lasts_for + a
            print("pos:", pos)
            if pos > number_of_days - 1:
                break
            tags_not_allowed[pos].add(tag_id)

print("\n\n\nFinished meal plan:\n", meals)
# Commit changes and close connection
con.commit()
con.close()
