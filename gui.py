"""
gui.py - sets up main interface and interactions
"""

import dearpygui.dearpygui as dpg
from oncollamaschemav3.validate import validate_json

from utils import call_openpipe_api, load_endpoints, load_env_vars, test_connection


class OpenPipeGUI:
    def __init__(self):
        self.api_key = None
        self.model = None
        self.connected = False
        self.endpoints = []

    def parse_escape_sequences(self, text):
        """
        Defensive measure to convert literal escapes
        """
        text = text.replace("\\n", "\n")
        text = text.replace("\\t", "\t")
        text = text.replace("\\r", "\r")
        return text

    def on_endpoint_changed(self):
        selected = dpg.get_value("endpoint_dropdown")
        self.model = selected
        dpg.set_value("status_text", "Testing connection...")
        success, message = test_connection(self.api_key, self.model)
        self.connected = success
        dpg.set_value("status_text", message)
        dpg.configure_item("status_indicator", default_value=success)

    def initialise(self):
        """
        Initialise GUI, test API connection
        """
        self.api_key = load_env_vars()
        self.endpoints = load_endpoints()

        if not self.api_key:
            dpg.set_value("status_text", "Error: Missing API key in .env")
            dpg.configure_item("status_indicator", default_value=False)
            return

        if not self.endpoints:
            dpg.set_value("status_text", "Error: No endpoints in endpoints.yaml")
            dpg.configure_item("status_indicator", default_value=False)
            return

        self.model = self.endpoints[0]
        dpg.configure_item(
            "endpoint_dropdown", items=self.endpoints, default_value=self.model
        )

        dpg.set_value("status_text", "Testing connection...")
        success, message = test_connection(self.api_key, self.model)
        self.connected = success
        dpg.set_value("status_text", message)
        dpg.configure_item("status_indicator", default_value=success)

    def on_input_changed(self):
        """
        Text input changes a formatted preview
        """
        input_text = dpg.get_value("input_text")
        formatted_text = self.parse_escape_sequences(input_text)
        dpg.set_value("preview_text", formatted_text)

    def on_infer_clicked(self):
        """
        Handle button click: Infer
        """
        if not self.connected:
            dpg.set_value("output_text", "Error: Not connected to API")
            return

        input_text = dpg.get_value("input_text")
        input_text = self.parse_escape_sequences(input_text)

        if not input_text.strip():
            dpg.set_value("output_text", "Error: Please enter some text")
            return

        dpg.set_value("output_text", "Processing...")
        dpg.configure_item("infer_button", enabled=False)

        success, result = call_openpipe_api(self.api_key, self.model, input_text)

        dpg.set_value("output_text", result)
        dpg.configure_item("infer_button", enabled=True)

        if success:
            is_valid, validation_msg, _ = validate_json(result)
            if is_valid:
                dpg.set_value("validation_status", "Output Validation Succeeded")
                dpg.configure_item("validation_status", color=(0, 255, 0))
            else:
                dpg.set_value(
                    "validation_status", f"Output Validation Failed: {validation_msg}"
                )
                dpg.configure_item("validation_status", color=(255, 0, 0))
        else:
            dpg.set_value("validation_status", "")
            dpg.configure_item("validation_status", color=(255, 255, 255))

    def create_gui(self):
        """
        Create primary interface
        """
        dpg.create_context()

        with dpg.window(label="OncoLlama GUI", tag="main_window"):
            # ENDPOINT SELECTION
            with dpg.group(horizontal=True):
                dpg.add_text("Endpoint:")
                dpg.add_combo(
                    tag="endpoint_dropdown",
                    items=[],
                    width=300,
                    callback=lambda: self.on_endpoint_changed(),
                )

            dpg.add_separator()

            # CONNECTION STATUS
            with dpg.group(horizontal=True):
                dpg.add_text("Connection Status:")
                dpg.add_checkbox(
                    tag="status_indicator", default_value=False, enabled=False
                )
                dpg.add_text("Initialising...", tag="status_text")

            dpg.add_separator()

            # MAIN CONTENT
            with dpg.group(horizontal=True):
                # LEFT PANE (Text Input/Formatted Preview)
                with dpg.child_window(width=500, height=600):
                    dpg.add_text("Enter / Paste Here:")
                    dpg.add_input_text(
                        tag="input_text",
                        multiline=True,
                        width=-1,
                        height=100,
                        default_value="",
                        tab_input=True,
                        callback=lambda: self.on_input_changed(),
                    )
                    dpg.add_button(
                        label="Infer",
                        tag="infer_button",
                        callback=lambda: self.on_infer_clicked(),
                        width=-1,
                        height=30,
                    )
                    dpg.add_separator()
                    dpg.add_text("Formatted Preview:")
                    dpg.add_text(tag="preview_text", default_value="", wrap=0)
                # RIGHT PANE (JSON Output)
                with dpg.child_window(width=-1, height=600):
                    dpg.add_text("Extracted JSON:")
                    dpg.add_text("", tag="validation_status", color=(255, 255, 255))
                    dpg.add_input_text(
                        tag="output_text",
                        multiline=True,
                        width=-1,
                        height=-1,
                        default_value="Results will appear here...",
                        readonly=True,
                    )

        dpg.create_viewport(title="OncoLlama GUI", width=1200, height=700)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("main_window", True)

        self.initialise()

    def run(self):
        dpg.start_dearpygui()
        dpg.destroy_context()  # destroys/de-allocates resources on exit
