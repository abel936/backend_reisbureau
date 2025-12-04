import requests
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration

def generate_captions(img_url):
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

    raw_image = Image.open(requests.get(img_url, stream=True).raw).convert('RGB')


    # unconditional image captioning
    inputs = processor(raw_image, return_tensors="pt")

    out = model.generate(**inputs)
    return processor.decode(out[0], skip_special_tokens=True)


url_ = "https://ack2511urlgenererenbb.blob.core.windows.net/images/7e0f5d6094f645bf8cd44e298f841fe9.png?se=2025-12-05T12%3A54%3A34Z&sp=r&sv=2025-11-05&sr=b&sig=J%2BKKPMFxCI6/V3IVhAK3Hti5laakP0eBoMJKzajlRb8%3D"
print(generate_captions(url_))