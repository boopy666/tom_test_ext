import gradio as gr
import os, sys
from exllamav2.generator import ExLlamaV2Sampler

# Find the path to the 'modules' directory relative to the current file
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # Move up to the 'extensions' directory
base_dir = os.path.dirname(parent_dir)  # Move up to the base 'text-generation-webui' directory
modules_path = os.path.join(base_dir, 'modules')

if modules_path not in sys.path:
    sys.path.append(modules_path)

from chat import generate_chat_prompt

# extension parameters
params = {
    "display_name": "Multi_Inference",
    "is_tab": False
}

# Initialize the extension state
multi_inference_state = {
    "active": False,
    "num_responses": 3,
    "temperature": 1.0,
    "dynamic_enabled": False,
    "temp_low": 1,
    "temp_high": 1,
    "dyntemp_exp": 1
}

def update_temp_high_range(temp_low_value, temp_high_value):
    if temp_high_value < temp_low_value:
        temp_high_value = temp_low_value
    return temp_high_value

# This function will be used to generate the UI components for the extension
def ui():
    with gr.Accordion("Multi-Inference Settings", open=True):
        enabled = gr.Checkbox(label="Enabled", value=multi_inference_state["active"])
        num_responses = gr.Number(label="Number of Responses", value=multi_inference_state["num_responses"], step=1)
        temperature = gr.Slider(label="Temperature", minimum=0, maximum=5, step=0.01, value=1.0)
        dynamic_enabled = gr.Checkbox(label="Dynamic Temp Enabled", value=multi_inference_state["dynamic_enabled"])
        if dynamic_enabled:
            temp_low = gr.Slider(label="Dynamic Temp - Low", minimum=0, maximum=5, step=0.01, value=1.0)
            temp_high = gr.Slider(label="Dynamic Temp - High", minimum=0, maximum=5, step=0.01, value=1.0)
            dyntemp_exp = gr.Slider(label="Dynamic Temp - Exponent", minimum=0, maximum=5, step=0.01, value=1.0)

        enabled.change(toggle_multi_inference, inputs=[enabled], outputs=[])
        num_responses.change(set_num_responses, inputs=[num_responses], outputs=[])
        temperature.change(set_temperature, inputs=[temperature], outputs=[])
        dynamic_enabled.change(set_dynamic_temp, inputs=[dynamic_enabled, temp_low, temp_high, dyntemp_exp], outputs=[])
        temp_low.change(set_dynamic_temp, inputs=[dynamic_enabled, temp_low, temp_high, dyntemp_exp], outputs=[])
        temp_high.change(set_dynamic_temp, inputs=[dynamic_enabled, temp_low, temp_high, dyntemp_exp], outputs=[])
        dyntemp_exp.change(set_dynamic_temp, inputs=[dynamic_enabled, temp_low, temp_high, dyntemp_exp], outputs=[])

# Handlers for UI component changes
def toggle_multi_inference(enabled):
    multi_inference_state["active"] = enabled

def set_num_responses(num_responses):
    multi_inference_state["num_responses"] = num_responses

def set_temperature(temp_value):
    multi_inference_state["temperature"] = temp_value

def set_dynamic_temp(dynamic_enabled, temp_low, temp_high, dyntemp_exp):
    multi_inference_state["dynamic_enabled"] = dynamic_enabled
    temp_high = update_temp_high_range(float(temp_low), float(temp_high))  # Ensure temp_high is not less than temp_low
    multi_inference_state["temp_low"] = temp_low
    multi_inference_state["temp_high"] = temp_high
    multi_inference_state["dyntemp_exp"] = dyntemp_exp
    # Additional logic for setting dynamic temperature can be added here if necessary

# Custom function to generate chat prompts for multi-inference
def custom_generate_chat_prompt(user_input, state, **kwargs):
    if not multi_inference_state["active"]:
        return chat.generate_chat_prompt(user_input, state, **kwargs)

    # Set the temperature according to the user settings
    state['temperature'] = multi_inference_state["temperature"]
    state['dynamic_temperature'] = multi_inference_state["dynamic_enabled"]
    state['dynatemp_low'] = multi_inference_state["temp_low"]
    state['dynatemp_high'] = multi_inference_state["temp_high"]
    state['dynatemp_exponent'] = multi_inference_state["dyntemp_exp"]

