import datetime
import re
import gradio as gr

class CharacterStats:
    SHIRT_SIZES = ["Medium", "Large", "X-Large", "XX-Large", "XXX-Large", "XXXX-Large", "XXXXX-Large"]
    MOODS = ["Happy", "Sad", "Excited", "Angry", "Scared"]
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
            self.weight += 1  # Add 1 lb for every excess of 500 calories
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
            string = re.sub(r"==END_DAY==", "", string)

        food_matches = re.findall(r"\{([^}]+):(\d+)\}", string)
        for _, cal in food_matches:
            character_stats.add_calories(int(cal))
            string = re.sub(r"\{[^}]+:\d+\}", "", string)

    return string

def custom_generate_chat_prompt(user_input, state, **kwargs):
    stats_context = "Use these stats to define your age, weight, BMI, Shirt size, Pant size, Current Calories consumed, mood and your realtionship status with {{user}}: " \
					f"Age: {character_stats.age}, Weight: {character_stats.weight} lbs, BMI: {character_stats.calculate_bmi()}, " \
                    f"Shirt Size: {character_stats.shirt_size}, Pant Size: {character_stats.pant_size}, " \
                    f"Current Calories: {character_stats.current_calories}, Max Calories: {character_stats.max_calories}, " \
                    f"Mood: {character_stats.mood}, Relationship Status: {character_stats.relationship_status}"
    result = chat.generate_chat_prompt(user_input, state, **kwargs)
    return f"{stats_context}\n{result}"

def ui():
    stats_display = gr.Markdown()
    end_day_button = gr.Button("End Day")
    food_input = gr.Textbox(placeholder="Add food item in format {food:calories}")
    add_food_button = gr.Button("Add Food")

    def update_stats_display():
        bmi = character_stats.calculate_bmi()
        return f"""
        **Age**: {character_stats.age}
        **Weight**: {character_stats.weight} lbs
        **BMI**: {bmi}
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

# Bind these functions to the appropriate handlers in your chat framework.
