import datetime
import re
import gradio as gr
import os
import sys

# Find the path to the 'modules' directory relative to the current file
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # Move up to the 'extensions' directory
base_dir = os.path.dirname(parent_dir)  # Move up to the base 'text-generation-webui' directory
modules_path = os.path.join(base_dir, 'modules')

if modules_path not in sys.path:
    sys.path.append(modules_path)

from chat import generate_chat_prompt

class CharacterStats:
    SHIRT_SIZES = ["Medium", "Large", "X-Large", "XX-Large", "XXX-Large", "XXXX-Large", "XXXXX-Large"]

    def __init__(self):
        self.age = 19
        self.weight = 170  # lbs
        self.height_inches = 67  # 5'7"
        self.current_calories = 0
        self.max_calories = 1620
        self.current_date = datetime.datetime(2009, 6, 15)  # June 15th, 2009
        self.update_clothing_sizes()

    def add_calories(self, calories):
        self.current_calories += calories

    def calculate_bmi(self):
        bmi_value = (self.weight / (self.height_inches ** 2)) * 703
        categories = ["Healthy", "Overweight", "Chubby", "Obese", "Super Obese", "Hyper Obese"]
        thresholds = [18.5, 25, 30, 35, 40, 45]
        for i, threshold in enumerate(thresholds):
            if bmi_value < threshold:
                return f"{bmi_value:.1f} ({categories[i]})"
        return f"{bmi_value:.1f} ({categories[-1]})"

    def calculate_bmr(self):
        return 655 + (4.35 * self.weight) + (4.7 * self.height_inches) - (4.7 * self.age)

    def calculate_fullness(self):
        # Calculate the percentage of max_calories consumed
        fullness_percentage = (self.current_calories / self.max_calories) * 100

        # Determine fullness category
        if fullness_percentage <= 20:
            return "Starving"
        elif fullness_percentage <= 40:
            return "Hungry"
        elif fullness_percentage <= 60:
            return "Content"
        elif fullness_percentage <= 80:
            return "Satiated"
        elif fullness_percentage <= 100:
            return "Stuffed"
        else:
            return "Overfed"

    def end_day(self):
        self.current_date += datetime.timedelta(days=1)
        # Check if it's her birthday (August 16th)
        if self.current_date.month == 8 and self.current_date.day == 16:
            self.age += 1  # Increment age
        excess_calories = self.current_calories - self.calculate_bmr()
        if excess_calories > 500:
            self.weight += int(excess_calories / 500)  # Add 1 lb for every excess of 500 calories
        self.current_calories = 0
        self.update_clothing_sizes()
        self.max_calories = self.calculate_bmr()

    def formatted_date(self):
        return self.current_date.strftime("%B %d, %Y")  # Format: "Month day, Year"

    def update_clothing_sizes(self):
        self.weight_diff = self.weight - 170  # Initial weight

        # Update shirt size and fit
        shirt_index = max(0, min(len(self.SHIRT_SIZES) - 1, self.weight_diff // 30))
        self.shirt_size = self.SHIRT_SIZES[shirt_index]
        if self.weight_diff % 30 <= 10:
            self.shirt_fit = "Loose Fit"
        elif self.weight_diff % 30 <= 20:
            self.shirt_fit = "Standard Fit"
        else:
            self.shirt_fit = "Tight Fit"

        # Update pant size and fit
        self.pant_size = 14 + (max(0, self.weight_diff // 15) * 2)  # Start from size 14 and increment by 2 for every 15 lbs
        if self.weight_diff % 15 <= 5:
            self.pant_fit = "Loose Fit"
        elif self.weight_diff % 15 <= 10:
            self.pant_fit = "Standard Fit"
        else:
            self.pant_fit = "Tight Fit"

    def reset_stats(self):
        self.age = 19
        self.weight = 170  # lbs
        self.height_inches = 67  # 5'7"
        self.current_calories = 0
        self.max_calories = 1620  # Reset to initial value
        self.current_date = datetime.datetime(2009, 6, 15)  # Reset to initial date
        self.update_clothing_sizes()

    def set_weight(self, new_weight):
        self.weight = new_weight
        self.update_clothing_sizes()
        self.max_calories = self.calculate_bmr()

    def set_age(self, new_age):
        self.age = new_age
        self.max_calories = self.calculate_bmr()

    def set_calories(self, new_calories):
        self.current_calories = new_calories

    def set_date(self, new_date):
        self.current_date = datetime.datetime.strptime(new_date, '%Y-%m-%d')

character_stats = CharacterStats()

def input_modifier(string, state, is_chat=False):
    if is_chat:
        if "==END_DAY==" in string:
            character_stats.end_day()
            string = re.sub(r"==END_DAY==", "", string).strip()

        if "==RESET==" in string:
            character_stats.reset_stats()
            string = re.sub(r"==RESET==", "", string).strip()

        # Pattern matching for stat overrides
        weight_match = re.search(r'weight==(\d+)', string)
        if weight_match:
            character_stats.set_weight(int(weight_match.group(1)))
            string = re.sub(r'weight==\d+', '', string)

        age_match = re.search(r'age==(\d+)', string)
        if age_match:
            character_stats.set_age(int(age_match.group(1)))
            string = re.sub(r'age==\d+', '', string)

        calories_match = re.search(r'calories==(\d+)', string)
        if calories_match:
            character_stats.set_calories(int(calories_match.group(1)))
            string = re.sub(r'calories==\d+', '', string)

        date_match = re.search(r'date==(\d{4}-\d{2}-\d{2})', string)
        if date_match:
            character_stats.set_date(date_match.group(1))
            string = re.sub(r'date==\d{4}-\d{2}-\d{2}', '', string)

        food_matches = re.findall(r"\{([^}]+):(\d+)\}", string)
        for match in food_matches:
            _, cal = match
            character_stats.add_calories(int(cal))
            string = re.sub(re.escape(match), "", string).strip()



    return string

def chat_input_modifier(text, visible_text, state):
    is_new_chat = len(state['history']['internal']) == 1
    end_day_called = "==END_DAY==" in text
    food_matches = re.findall(r"\{([^}]+):(\d+)\}", text)
    is_story = "STORY:" in text
    reset_stats = "==RESET==" in text
    weight_match = re.search(r'weight==(\d+)', text)
    age_match = re.search(r'age==(\d+)', text)
    calories_match = re.search(r'calories==(\d+)', text)
    date_match = re.search(r'date==(\d{4}-\d{2}-\d{2})', text)

    # Process end day command
    end_day_message = []
    if end_day_called:
        character_stats.end_day()
        if character_stats.current_date.month == 8 and character_stats.current_date.day == 16:
            end_day_message.append(
                f"\n*It's the start of a new day... And it's Maddy's birthday! You are now {character_stats.age}!*\n")
        else:
            end_day_message.append("\n*It's the start of a new day!*\n")
        visible_text = text.replace("==END_DAY==", "").strip()

    if reset_stats:
        character_stats.reset_stats()
        visible_text = visible_text.replace("==RESET==", "").strip()

    food_messages = []

    for food_item, calories in food_matches:
        character_stats.add_calories(int(calories))
        fullness_status = character_stats.calculate_fullness()
        food_messages.append(f"\n*Maddy just ate {food_item}*\n*After eating this, Maddy is feeling {fullness_status}.*")
        visible_text = visible_text.replace(f"{{{food_item}:{calories}}}", "").strip()

    if weight_match:
        character_stats.set_weight(int(weight_match.group(1)))
        match_str = weight_match.group(0)
        text = text.replace(match_str, "").strip()

    if age_match:
        character_stats.set_age(int(age_match.group(1)))
        match_str = age_match.group(0)
        text = text.replace(match_str, "").strip()

    if calories_match:
        character_stats.set_calories(int(calories_match.group(1)))
        # Extract the matched pattern as a string
        match_str = calories_match.group(0)
        # Replace the matched string with an empty string
        text = text.replace(match_str, "").strip()

    if date_match:
        character_stats.set_date(date_match.group(1))
        match_str = date_match.group(0)
        text = text.replace(match_str, "").strip()

    # Create stats context
    stats_context = (
        f"[Today's date is {character_stats.formatted_date()}. Maddy is now {character_stats.age} years old, "
        f"5'7 inches tall, and currently weighs {character_stats.weight} lbs, so with that her BMI is {character_stats.calculate_bmi()} "
        f"and she has gained {character_stats.weight_diff} lbs since June 15th 2009. She currently wears a {character_stats.shirt_size} "
        f"shirt ({character_stats.shirt_fit}), and has a pant size {character_stats.pant_size} US women's ({character_stats.pant_fit}). "
        f"So far she has consumed {character_stats.current_calories} out of {character_stats.max_calories} calories today.]"
    )

    # Append food and end day messages to the stats context
    if end_day_message:
        stats_context += "\n".join(end_day_message)

    if food_messages:
        stats_context += "\n".join(food_messages)

    # Check for story and modify text accordingly
    if is_story and is_new_chat:
        modified_text = f"{stats_context}\n{text}"
        modified_visible_text = f"{stats_context}\n{visible_text}"
    elif is_new_chat or end_day_called or food_matches or reset_stats:
        modified_text = f"{stats_context}\n{text}"
        modified_visible_text = f"{stats_context}\n{visible_text}"
    elif weight_match or age_match or calories_match or date_match:
        modified_text = f"{stats_context}\n{text}"
        modified_visible_text = f"{stats_context}\n{visible_text}"
    else:
        modified_text = "TOM: " + text
        modified_visible_text = "TOM: " + visible_text

    if weight_match:
        match_str = weight_match.group(0)
        visible_text = visible_text.replace(match_str, "").strip()

    if age_match:
        match_str = age_match.group(0)
        visible_text = visible_text.replace(match_str, "").strip()

    if calories_match:
        # Extract the matched pattern as a string
        match_str = calories_match.group(0)
        # Replace the matched string with an empty string
        visible_text = visible_text.replace(match_str, "").strip()

    if date_match:
        match_str = date_match.group(0)
        visible_text = visible_text.replace(match_str, "").strip()
        
    if reset_stats:
        text = text.replace("==RESET==", "").strip()

    if end_day_called:
        text = text.replace("==END_DAY==", "").strip()

    text = modified_text
    visible_text = modified_visible_text

    return text, visible_text


def output_modifier(string, state, is_chat=False):

    if "==END_DAY==" in string:
        string += "\n*It's the start of a new day!*"
        string = re.sub(r"==END_DAY==", "", string).strip()

    # Regex to find patterns like {food:calories}
    food_matches = re.findall(r"\{([^}]+):(\d+)\}", string)

    # For each match, update character stats
    for food, cal in food_matches:
        character_stats.add_calories(int(cal))
        # Optionally, add a confirmation message to the response
        string += f"\n(Added {cal} calories from {food} to the stats)"

    return string