import flet as ft
#from globals import context, model_list, llm_model, stop_response, model, prompt, chain, knowlage_base_added, chat_id, collection
#import globals
from ui import build_ui


def main(page: ft.Page):
    build_ui(page)


if __name__ == "__main__":
    try:
        ft.app(target=main,  assets_dir="assets", view=ft.FLET_APP)
    except Exception as e:
        print(f"Error with page: {e}")

