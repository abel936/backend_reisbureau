import requests
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
from chatbb import Afb_generen_met_url

def generate_captions(img_url):
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

    raw_image = Image.open(requests.get(img_url, stream=True).raw).convert('RGB')


    # unconditional image captioning
    inputs = processor(raw_image, return_tensors="pt")

    out = model.generate(**inputs)
    return processor.decode(out[0], skip_special_tokens=True)


url_, img_ = Afb_generen_met_url()

print(img_)
print(generate_captions(url_))