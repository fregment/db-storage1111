import base64
from io import BytesIO
import os
import re
import modules.scripts as scripts
import gradio as gr
# from pymongo import MongoClient
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
# from dotenv import load_dotenv

# load_dotenv()  # take environment variables from .env.

# mongo_host = os.environ.get('DB_HOST', 'localhost')
# mongo_port = int(os.environ.get('DB_PORT', 27017))
mongo_username = os.environ.get('DB_USER', '')
mongo_password = os.environ.get('DB_PASS', '')
mongo_cluster = os.environ.get('DB_CLUSTER', '')


# Rewrite this to use supabase instead of mongo
# images to be stored in supabase storage
# creds = f"{mongo_username}:{mongo_password}@" if mongo_username and mongo_password else ""
# client = MongoClient(f"mongodb://{creds}{mongo_host}:{mongo_port}/")

uri = f"mongodb+srv://{mongo_username}:{mongo_password}@{mongo_cluster}/?retryWrites=true&w=majority"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))


def get_collection(database_name, collection_name):
    db = client[database_name]
    collection = db[collection_name]
    return collection

class Scripts(scripts.Script):
    def title(self):
        return "Mongo Storage"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        checkbox_save_to_db = gr.inputs.Checkbox(label="Save to DB", default=False)
        database_name = gr.inputs.Textbox(label="Database Name", default="StableDiffusion")
        collection_name = gr.inputs.Textbox(label="Collection Name", default="Automatic1111")
        return [checkbox_save_to_db, database_name, collection_name]

    def postprocess(self, p, processed,checkbox_save_to_db,database_name,collection_name):
        collection = get_collection(database_name, collection_name) if checkbox_save_to_db else None
        if collection is None:
            return True
        
        for i in range(len(processed.images)):

            # Extract image information
            regex = r"Steps:.*$"
            seed = processed.seed
            prompt = processed.prompt
            neg_prompt = processed.negative_prompt
            info = re.findall(regex, processed.info, re.M)[0]
            input_dict = dict(item.split(": ") for item in str(info).split(", "))
            steps = int(input_dict["Steps"])
            seed = int(input_dict["Seed"])
            sampler = input_dict["Sampler"]
            cfg_scale = float(input_dict["CFG scale"])
            size = tuple(map(int, input_dict["Size"].split("x")))
            model_hash = input_dict["Model hash"]
            model = input_dict["Model"]

            image = processed.images[i]
            buffer = BytesIO()
            image.save(buffer, "png")
            image_bytes = buffer.getvalue()

            collection.insert_one({
                "prompt": prompt, 
                "negative_prompt": neg_prompt, 
                "steps": int(steps), 
                "seed": int(seed), 
                "sampler": sampler,
                "cfg_scale": float(cfg_scale), 
                "size": size, 
                "model_hash": model_hash, 
                "model": model, 
                "image": image_bytes
            })
        return True
