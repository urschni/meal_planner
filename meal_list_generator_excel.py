import pandas as pd
import logging
import os.path
import random

# Markdown and PDF export
from mdutils.mdutils import MdUtils
import pypandoc

excel_data_meals = pd.read_excel("meals_and_tags.xlsx", sheet_name="meals")
excel_data_tags = pd.read_excel("meals_and_tags.xlsx", sheet_name="tags")
excel_data_conf = pd.read_excel("meals_and_tags.xlsx", sheet_name="conf")

logging.basicConfig(level=logging.DEBUG)

def get_random_meal_without_tags(tags):
    possible_meals = [a for a in excel_data_meals.values if not any (b in a[3] for b in tags)]
    logging.debug("possible meals: %s" % possible_meals)
    if possible_meals:
        return random.choice(possible_meals)
#print("all meals:", [a for a in excel_data_meals.values])
#print(excel_data_meals["Name"])
#print("rand meal:", get_random_meal_without_tags(["Nudeln"]))

def get_tag_by_id(tag):
    for current_tag in excel_data_tags.values:
        if tag in current_tag:
            return current_tag
#print("Nudeln Tag:", get_tag_by_id("Nudeln")[2], type(get_tag_by_id("Nudeln")))

# Create plan
start_date = excel_data_conf["Startdatum"][0].strftime("%Y-%m-%d")
end_date = excel_data_conf["Enddatum"][0].strftime("%Y-%m-%d")
days = pd.date_range(start=start_date, end=end_date)
number_of_days = len(days)
excluded_tags = [] if pd.isna(excel_data_conf["Ausgeschlossene Tags"][0]) else excel_data_conf["Ausgeschlossene Tags"][0].split(", ")
tags_not_allowed = [set(excluded_tags) for a in range(number_of_days)]
meals = [None] * number_of_days

#all_meals = get_meals_without_tags(db, 0)

for current_day in range(number_of_days):
    logging.debug("Meals on day %s: %s" % (current_day, meals))
    logging.debug("tags not allowed on day %s: %s" % (current_day, tags_not_allowed))
    if meals[current_day] is not None:
        logging.debug("Skip day %s" % current_day)
        continue
    # Get banned tags
    banned_tags = tags_not_allowed[current_day]
    # Get all possible meals
    selected_meal = get_random_meal_without_tags(tuple(banned_tags))
    # Select meal
    meal_name, meal_description, meal_lasts_for, meal_tags = selected_meal
    # Check if meal_lasts_for is a range and not a number:
    if isinstance(meal_lasts_for, str) and '-' in meal_lasts_for:
        from_to = meal_lasts_for.split('-')
        meal_lasts_for = random.choice(range(int(from_to[0]), int(from_to[1])+1))
    meal_tags = meal_tags.split(", ")
    logging.debug("meal tags: %s" % meal_tags)
    for a in range(meal_lasts_for):
        if current_day + a < number_of_days:
            meals[current_day + a] = meal_name
        else:
            break
    for tag in meal_tags:
        logging.debug("tag: %s" % tag)
        tag_info = get_tag_by_id(tag)
        logging.debug("Info to tag %s: %s" % (tag, tag_info))
        tag_name, tag_description, tag_duration = tag_info
        logging.debug("tag duration: %s" % tag_duration)
        for a in range(tag_duration):
            pos = current_day + meal_lasts_for + a
            logging.debug("pos: %s" % pos)
            if pos > number_of_days - 1:
                break
            tags_not_allowed[pos].add(tag)

logging.info("\n\n\nFinished meal plan:\n%s" % meals)

# Export to Markdown
export_filename = "Essensplan"
md = MdUtils(file_name=export_filename, title="Essensplan vom {} bis {}".format(start_date, end_date))
table_content = [item for subl in list(zip([str(d.strftime("%Y-%m-%d")) for d in days], meals)) for item in subl]
md.new_table(columns=2, rows=number_of_days, text=table_content)
md.create_md_file()
# Export from Markdown to PDF
pypandoc.convert_file(export_filename + ".md", "pdf", outputfile=export_filename + ".pdf")
os.remove(export_filename + ".md")