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
    MOODS = ["Happy", "Sad", "Excited", "Angry", "Scared", "Nervous", "Relaxed", "Curious", "Indifferent", "Surprised"]
    RELATIONSHIPS = ["Acquaintance", "Friend", "Best Friend", "Crush", "Romantic", "Lover"]

    def __init__(self):
        self.age = 19
        self.weight = 170  # lbs
        self.height_inches = 67  # 5'7"
        self.current_calories = 0
        self.max_calories = 3500  # Arbitrary value for calories needed to gain weight
        self.current_date = datetime.datetime.now()
        self.mood = "Happy"
        self.relationship_status = "Acquaintance"
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

    def end_day(self):
        self.current_date += datetime.timedelta(days=1)
        excess_calories = self.current_calories - self.calculate_bmr()
        if excess_calories > 500:
            self.weight += excess_calories % 500  # Add 1 lb for every excess of 500 calories
        self.current_calories = 0
        self.update_clothing_sizes()

    def update_clothing_sizes(self):
        weight_diff = self.weight - 170  # Initial weight
        shirt_index = max(0, min(len(self.SHIRT_SIZES) - 1, weight_diff // 30))
        self.shirt_size = f"{self.SHIRT_SIZES[shirt_index]}"
        self.pant_size = 14 + (max(0, weight_diff // 15) * 2)  # Start from size 14 and increment by 2 for every 15 lbs

    def change_mood(self, mood):
        if mood in self.MOODS:
            self.mood = mood

    def change_relationship_status(self, status):
        if status in self.RELATIONSHIPS:
            self.relationship_status = status

character_stats = CharacterStats()

def input_modifier(string, state, is_chat=False):
    if is_chat:
        if "==END_DAY==" in string:
            character_stats.end_day()
            string = re.sub(r"==END_DAY==", "", string).strip()

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

    # Process end day command
    if end_day_called:
        character_stats.end_day()
        text = text.replace("==END_DAY==", "").strip()

    # Process added food
    for food_item, calories in food_matches:
        character_stats.add_calories(int(calories))
        text = text.replace(f"{{{food_item}:{calories}}}", "").strip()

    # Create stats context
    stats_context = (
        f"[You are {character_stats.age} years old, 5'7 inches tall, and currently weigh {character_stats.weight} lbs, "
        f"so with that your BMI is {character_stats.calculate_bmi()}. You currently wear a {character_stats.shirt_size} "
        f"shirt, and have a pant size {character_stats.pant_size} US women's. So far you have consumed "
        f"{character_stats.current_calories} calories today. You are feeling {character_stats.mood}. As for your "
        f"relationship with Tom, you two are considered {character_stats.relationship_status}.]"
    )

    # Initialize reminder messages list and check for keywords
    reminder_messages = []
    if "weight" in text or "weigh" in text:
        reminder_messages.append(f"[Reminder: You currently weigh {character_stats.weight} lbs]")
    if "pant size" in text:
        reminder_messages.append(f"[Reminder: Your pant size is {character_stats.pant_size} US women's]")
    if "shirt size" in text:
        reminder_messages.append(f"[Reminder: You currently wear a {character_stats.shirt_size} shirt]")

    # Append reminders to the stats context
    if reminder_messages:
        stats_context += "\n" + "\n".join(reminder_messages)

    # Modify text based on different conditions
    if is_story and is_new_chat:
        modified_text = f"{stats_context}\n{text}"
        modified_visible_text = f"{stats_context}\n{visible_text}"
    elif is_story:
        modified_text = text.replace("STORY: ", "").strip()
        modified_visible_text = visible_text.replace("STORY: ", "").strip()
    elif is_new_chat or end_day_called or food_matches:
        modified_text = f"{stats_context}\n{text}"
        modified_text = modified_text.replace("==END_DAY==", "").strip()
        modified_text = modified_text.replace(f"{{{food_item}:{calories}}}", "").strip()
        modified_visible_text = f"{stats_context}\n{visible_text}"
        modified_visible_text = modified_visible_text.replace("==END_DAY==", "").strip()
        modified_visible_text = modified_visible_text.replace(f"{{{food_item}:{calories}}}", "").strip()
    else:
        modified_text = "TOM: " + text
        modified_visible_text = "TOM: " + visible_text

    return modified_text, modified_visible_text


def output_modifier(string, state, is_chat=False):
    mood_pattern = re.compile(r"<(" + "|".join(CharacterStats.MOODS) + ")>")
    match = mood_pattern.search(string)
    if match:
        new_mood = match.group(1)
        character_stats.change_mood(new_mood)
        string = mood_pattern.sub("", string).strip()
        string += f" Maddy is now feeling {new_mood}."

    if "==END_DAY==" in string:
        string += "\n*It's the start of a new day!*"
        string = re.sub(r"==END_DAY==", "", string).strip()

        # Append a message immediately after processing a food item command
    food_matches = re.findall(r"\{([^}]+):(\d+)\}", string)
    for match in food_matches:
        string += f"\n*Tom just fed you {match[0]}*"
        string = re.sub(re.escape(match[0]), "", string).strip()

    return string

# UI for reflecting character stats and updates
def ui():
    stats_display = gr.Markdown()
    end_day_button = gr.Button("End Day")
    food_input = gr.Textbox(placeholder="Add food item in format {food:calories}")
    add_food_button = gr.Button("Add Food")

    def update_stats_display():
        return f"""
        **Age**: {character_stats.age}
        **Weight**: {character_stats.weight} lbs
        **BMI**: {character_stats.calculate_bmi()}
        **Shirt Size**: {character_stats.shirt_size}
        **Pant Size**: {character_stats.pant_size}
        **Current Calories**: {character_stats.current_calories}
        **Max Calories**: {character_stats.max_calories}
        **Mood**: {character_stats.mood}
        **Relationship Status**: {character_stats.relationship_status}
        """

    def end_day():
        character_stats.end_day()
        return update_stats_display()

    def add_food(food):
        match = re.match(r"\{([^}]+):(\d+)\}", food)
        if match:
            _, calories = match.groups()
            character_stats.add_calories(int(calories))
        return update_stats_display()

    end_day_button.click(fn=end_day, inputs=[], outputs=[stats_display])
    add_food_button.click(fn=add_food, inputs=[food_input], outputs=[stats_display])

    return gr.Column(stats_display, end_day_button, food_input, add_food_button)

params = {
    "display_name": "Dating Sim Character Tracker",
    "is_tab": True,
}
