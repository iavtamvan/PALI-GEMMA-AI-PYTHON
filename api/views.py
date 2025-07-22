from ninja import NinjaAPI, File, UploadedFile, Form
from gradio_client import Client, handle_file
from PIL import Image
from fastapi.responses import JSONResponse  # tambahkan di atas


from .models import ImageDetection

import pathlib
import os
import re
import json

api = NinjaAPI()

# Hardcoded Hugging Face Token
HF_TOKEN = ""  # <-- Ganti dengan token milikmu

def normalize_coordinates(coord: str, img_x, img_y):
	detect_pattern = r'<loc(\d+)>'
	detect_matches = re.findall(detect_pattern, coord)

	numbers = [int(d) for d in detect_matches]
	numbers[0] = int((numbers[0] / 1024) * img_y)
	numbers[1] = int((numbers[1] / 1024) * img_x)
	numbers[2] = int((numbers[2] / 1024) * img_y)
	numbers[3] = int((numbers[3] / 1024) * img_x)

	return numbers

@api.post('/detect')
def detect(request, prompt: Form[str], image: File[UploadedFile], width: Form[int], height: Form[int]):
	prompt = prompt.lower().strip()
	prompt_word = prompt.split()

	prompt_obj = ImageDetection.objects.create(
		prompt=prompt,
		image=image
	)

	cwd = pathlib.Path(os.getcwd())
	image_path = pathlib.Path(prompt_obj.image.url[1:])
	img_path = pathlib.Path(cwd, image_path)
	media_path = os.path.join(os.getcwd(), 'media/images/')

	img = Image.open(img_path).convert('RGB')
	resized_img = img.resize((width, height), Image.Resampling.LANCZOS)
	resized_img_path = os.path.join(media_path, 'resized_' + str(image))
	resized_img.save(resized_img_path)

	task = prompt_word[0]

	if task == "segment":
		client = Client("gokaygokay/Florence-2")
		prompt = prompt.replace("segment ", "")
		labels = prompt.split("; ")

		polygons = {'polygons': [], 'labels': labels}
		for label in labels:
			result = client.predict(
				image=handle_file(resized_img_path),
				task_prompt="Referring Expression Segmentation",
				text_input="<REFERRING_EXPRESSION_SEGMENTATION>" + label,
				model_id="microsoft/Florence-2-large",
				api_name="/process_image"
			)
			result = json.loads(result[0].replace("'", '"'))
			polygons['polygons'].extend(result['<REFERRING_EXPRESSION_SEGMENTATION>']['polygons'])

		return polygons

	elif task == "caption":
		from transformers import BlipProcessor, BlipForConditionalGeneration
		import torch

		processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base", token=HF_TOKEN)
		model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base", token=HF_TOKEN)

		inputs = processor(Image.open(resized_img_path).convert("RGB"), return_tensors="pt")
		output = model.generate(**inputs)
		caption = processor.decode(output[0], skip_special_tokens=True)
		# print(json.dumps({"result": caption}, indent=2), flush=True)
		print(json.dumps({ "response": caption }, indent=2), flush=True)

		return { "response": caption }

	elif task == "vqa":
		from transformers import ViltProcessor, ViltForQuestionAnswering

		question = prompt.replace("vqa ", "")
		processor = ViltProcessor.from_pretrained("dandelin/vilt-b32-finetuned-vqa", token=HF_TOKEN)
		model = ViltForQuestionAnswering.from_pretrained("dandelin/vilt-b32-finetuned-vqa", token=HF_TOKEN)

		image_pil = Image.open(resized_img_path).convert("RGB")
		encoding = processor(image_pil, question, return_tensors="pt")
		outputs = model(**encoding)
		logits = outputs.logits
		idx = logits.argmax(-1).item()
		answer = model.config.id2label[idx]
		result = [
			{
				"label": answer,
				"coordinates": [0, 0, 0, 0]
			}
		]

		print(json.dumps({"question": question, "result": result}, indent=2), flush=True)

		return {"result": result}

	else:
		return {"error": "Unsupported task. Use 'segment', 'caption', or 'vqa' as the first word in prompt."}
