import os
import base64
import requests
import time
import math
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont, ImageOps
from io import BytesIO
from rembg import remove

# --- INITIAL SETUP ---
load_dotenv()
app = Flask(__name__, static_folder='../frontend', static_url_path='')

# --- LOAD API KEY ---
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
if not STABILITY_API_KEY:
    print("CRITICAL ERROR: STABILITY_API_KEY not found in .env file.")

# --- ADVANCED HELPER FUNCTIONS for DESIGN & COLOR ---

def get_color_palette(image, num_colors=3):
    """Extracts a palette of the most dominant colors from an image."""
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    image = image.resize((100, 100))
    colors = {}
    for count, (r, g, b, a) in image.getcolors(image.size[0] * image.size[1]):
        if a > 128:
            if (r > 240 and g > 240 and b > 240) or (r < 15 and g < 15 and b < 15):
                continue
            colors[(r, g, b)] = colors.get((r, g, b), 0) + count
            
    if not colors:
        return [(0, 0, 0), (100, 100, 100), (255, 255, 255)] # Default black/grey/white
        
    sorted_colors = sorted(colors.items(), key=lambda item: item[1], reverse=True)
    palette = [color[0] for color in sorted_colors[:num_colors]]
    while len(palette) < 3:
        palette.append((50, 50, 50))
    return palette

def describe_color(rgb):
    """Creates a simple text description of an RGB color for the AI prompt."""
    r, g, b = rgb
    if r > g and r > b:
        if r > 150: return "vibrant red" if g < 100 else "orange"
        else: return "deep red"
    if g > r and g > b:
        if g > 150: return "bright green"
        else: return "dark green"
    if b > r and b > g:
        if b > 150: return "sky blue"
        else: return "deep blue"
    if r > 200 and g > 200 and b < 100: return "golden yellow"
    return "neutral tone"

def draw_text_with_shadow(draw, position, text, font, fill_color, shadow_color=(0,0,0,100)):
    """Draws text with a soft drop shadow for a professional look."""
    x, y = position
    draw.text((x+2, y+2), text, font=font, fill=shadow_color)
    draw.text((x, y), text, font=font, fill=fill_color)
    
def draw_starburst(draw, center, points, outer_radius, inner_radius, fill_color):
    """Draws a starburst shape for promotions."""
    angle = 2 * math.pi / points
    star_points = []
    for i in range(points):
        outer_x = center[0] + outer_radius * math.cos(i * angle)
        outer_y = center[1] + outer_radius * math.sin(i * angle)
        star_points.append((outer_x, outer_y))
        inner_x = center[0] + inner_radius * math.cos(i * angle + angle / 2)
        inner_y = center[1] + inner_radius * math.sin(i * angle + angle / 2)
        star_points.append((inner_x, inner_y))
    draw.polygon(star_points, fill=fill_color)

# --- API ENDPOINT for PROMOTIONAL POSTERS ---
@app.route('/api/generate_poster', methods=['POST'])
def generate_poster():
    data = request.json
    
    logo_image = None
    brand_palette = []
    if data.get('logo_base64'):
        logo_data = base64.b64decode(data['logo_base64'])
        logo_image_with_bg = Image.open(BytesIO(logo_data))
        logo_image = remove(logo_image_with_bg)
        if data.get('use_logo_colors'):
            brand_palette = get_color_palette(logo_image_with_bg)
    
    style_prompts = {
        "digital-art": f"A vibrant, professional digital illustration poster of a {data['business_type']} scene.",
        "photographic": f"A stunning, professional photograph of a {data['business_type']} scene.",
        "analog-film": f"An artistic, retro photo of a {data['business_type']} scene, shot on analog film."
    }
    style_preset = data.get('style', 'digital-art')
    prompt_text = style_prompts.get(style_preset, style_prompts['digital-art'])
    
    color_palette_choice = data.get('color_palette', 'auto')
    if color_palette_choice != 'auto':
        color_map = {
            "warm": "warm tones like reds, oranges, and yellows",
            "cool": "cool tones like blues, greens, and purples",
            "vibrant": "vibrant, saturated, and colorful tones",
            "pastel": "soft, pastel, and muted tones"
        }
        prompt_text += f" The main colors should be {color_map.get(color_palette_choice)}."
    elif brand_palette and data.get('use_logo_colors'):
        color_descriptions = [describe_color(c) for c in brand_palette]
        prompt_text += f" The main colors should be {', '.join(color_descriptions)}."

    prompt_text += " --no text, words, letters, typography"

    try:
        response = requests.post(
            f"https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
            headers={"Authorization": f"Bearer {STABILITY_API_KEY}"},
            json={ "text_prompts": [{"text": prompt_text}], "steps": 40, "width": 1024, "height": 1024, "style_preset": style_preset }
        )
        response.raise_for_status()
        image_data = base64.b64decode(response.json()["artifacts"][0]["base64"])
        image = Image.open(BytesIO(image_data))
        draw = ImageDraw.Draw(image)

    except Exception as e:
        return jsonify({"error": f"Failed during image generation: {str(e)}"}), 500
        
    try:
        font_brand = ImageFont.truetype("Poppins-Bold.ttf", 40)
        font_headline = ImageFont.truetype("Poppins-ExtraBold.ttf", 90)
    except IOError:
        return jsonify({"error": "Font files not found on server."}), 500

    padding = 60
    if logo_image:
        logo_image.thumbnail((250, 250)) 
        image.paste(logo_image, (padding, padding), logo_image)
    
    star_center = (image.width - 280, image.height - 280)
    star_color = brand_palette[1] if len(brand_palette) > 1 else (227, 28, 28)
    draw_starburst(draw, star_center, 16, 220, 170, star_color)
    headline_bbox = font_headline.getbbox(data['headline'])
    headline_width = headline_bbox[2] - headline_bbox[0]
    headline_pos = (star_center[0] - headline_width / 2, star_center[1] - font_headline.getbbox(data['headline'])[3] / 2)
    draw_text_with_shadow(draw, headline_pos, data['headline'], font_headline, (255, 255, 255))
    
    brand_text = f"{data['business_name']} | {data['location']}"
    brand_bbox = font_brand.getbbox(brand_text)
    brand_pos = (padding, image.height - padding - brand_bbox[3])
    draw_text_with_shadow(draw, brand_pos, brand_text, font_brand, (255,255,255))

    filename = f"generated_poster_{int(time.time())}.png"
    filepath = os.path.join("../frontend", filename)
    image.save(filepath)
    return jsonify({"image_url": filename})


# --- DEDICATED API ENDPOINT for FESTIVAL POSTERS ---
@app.route('/api/generate_festival_poster', methods=['POST'])
def generate_festival_poster():
    data = request.json
    
    logo_image = None
    brand_palette = []
    primary_color = (255, 255, 255)
    if data.get('logo_base64'):
        logo_data = base64.b64decode(data['logo_base64'])
        logo_image_with_bg = Image.open(BytesIO(logo_data))
        logo_image = remove(logo_image_with_bg)
        if data.get('use_logo_colors'):
            brand_palette = get_color_palette(logo_image_with_bg)
            primary_color = brand_palette[0] if brand_palette else (255,255,255)
    
    festival_prompts = {
        "Diwali": "A beautiful, artistic background for Diwali, with motifs of elegant lights, glowing diyas, and festive rangoli patterns.",
        "Holi": "A vibrant, artistic background for Holi, with dynamic splashes of colorful powder paint (gulal) and joyous energy.",
        "Navratri": "An elegant, artistic background for Navratri, with patterns inspired by traditional dandiya sticks, garba dance, and the Goddess Durga.",
        "Christmas": "A classic, artistic background for Christmas, with themes of festive ornaments, decorated pine trees, and snowflakes.",
        "Eid": "A sophisticated, artistic background for Eid, featuring an Islamic crescent moon, stars, glowing lanterns, and elegant geometric patterns.",
        "Ganesh Chaturthi": "A devotional, artistic background for Ganesh Chaturthi, featuring a beautiful illustration of Lord Ganesha, with modak sweets and hibiscus flowers."
    }
    style_preset = data.get('style', 'digital-art')
    festival = data.get('festival', 'Diwali')
    prompt_text = festival_prompts.get(festival, festival_prompts['Diwali'])
    
    if brand_palette and data.get('use_logo_colors'):
        color_descriptions = [describe_color(c) for c in brand_palette]
        prompt_text += f" The primary color palette should be heavily inspired by {', '.join(color_descriptions)}."
        
    prompt_text += f" Style: {style_preset}. --no text, words, letters, typography"

    try:
        response = requests.post(
            f"https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
            headers={"Authorization": f"Bearer {STABILITY_API_KEY}"},
            json={ "text_prompts": [{"text": prompt_text}], "steps": 40, "width": 1024, "height": 1024, "style_preset": style_preset }
        )
        response.raise_for_status()
        image_data = base64.b64decode(response.json()["artifacts"][0]["base64"])
        image = Image.open(BytesIO(image_data)).convert("RGBA")
        draw = ImageDraw.Draw(image)

    except Exception as e:
        return jsonify({"error": f"Failed during image generation: {str(e)}"}), 500
        
    try:
        font_festival = ImageFont.truetype("Poppins-ExtraBold.ttf", 80)
        font_greeting = ImageFont.truetype("Poppins-Bold.ttf", 50)
        font_brand = ImageFont.truetype("Poppins-Bold.ttf", 40)
    except IOError:
        return jsonify({"error": "Font files not found on server."}), 500
    
    padding = 60
    
    greeting_bbox = font_greeting.getbbox(data['greeting'])
    greeting_width = greeting_bbox[2] - greeting_bbox[0]
    greeting_pos = (image.width - greeting_width - padding, padding)
    draw_text_with_shadow(draw, greeting_pos, data['greeting'], font_greeting, (255, 255, 255))
    
    festival_bbox = font_festival.getbbox(festival)
    festival_width = festival_bbox[2] - festival_bbox[0]
    festival_pos = (image.width - festival_width - padding, padding + 60)
    draw_text_with_shadow(draw, festival_pos, festival, font_festival, primary_color)

    if logo_image:
        logo_image.thumbnail((250, 250))
        image.paste(logo_image, (padding, padding), logo_image)

    brand_text = f"{data['business_name']} | {data['location']}"
    brand_bbox = font_brand.getbbox(brand_text)
    brand_width = brand_bbox[2] - brand_bbox[0]
    brand_pos = (image.width - brand_width - padding, image.height - padding - brand_bbox[3])
    draw_text_with_shadow(draw, brand_pos, brand_text, font_brand, (255,255,255))

    filename = f"generated_poster_{int(time.time())}.png"
    filepath = os.path.join("../frontend", filename)
    image.save(filepath)
    return jsonify({"image_url": filename})


# --- "DESIGNER" API ENDPOINT for MENU CREATOR ---
@app.route('/api/generate_menu', methods=['POST'])
def generate_menu():
    data = request.json
    
    try:
        A4_WIDTH, A4_HEIGHT = 2480, 3508
        
        logo_data = base64.b64decode(data['logo_base64'])
        logo_image_with_bg = Image.open(BytesIO(logo_data))
        logo_image = remove(logo_image_with_bg)
        
        brand_palette = get_color_palette(logo_image_with_bg)
        primary_color = brand_palette[0]
        secondary_color = brand_palette[1] if len(brand_palette) > 1 else (100, 100, 100)
        background_tint = tuple(int(c + (255 - c) * 0.95) for c in secondary_color)

        menu = Image.new('RGB', (A4_WIDTH, A4_HEIGHT), background_tint)
        draw = ImageDraw.Draw(menu)
        
        font_title = ImageFont.truetype("Poppins-ExtraBold.ttf", 180)
        font_contact = ImageFont.truetype("Poppins-Regular.ttf", 70)
        font_item = ImageFont.truetype("Poppins-Bold.ttf", 60)
        font_price = ImageFont.truetype("Poppins-Regular.ttf", 60)

        padding = 200
        header_height = 900
        
        draw.rectangle([(0, 0), (A4_WIDTH, header_height)], fill=primary_color)
        
        logo_image.thumbnail((500, 500))
        logo_x = int((A4_WIDTH - logo_image.width) / 2)
        logo_y = padding - 50
        menu.paste(logo_image, (logo_x, logo_y), logo_image)
        
        title_bbox = font_title.getbbox(data['business_name'])
        title_width = title_bbox[2] - title_bbox[0]
        title_pos = (int((A4_WIDTH - title_width) / 2), logo_y + logo_image.height + 30)
        draw.text(title_pos, data['business_name'], font=font_title, fill=(255, 255, 255))

        contact_bbox = font_contact.getbbox(data['contact_info'])
        contact_width = contact_bbox[2] - contact_bbox[0]
        contact_pos = (int((A4_WIDTH - contact_width) / 2), title_pos[1] + 200)
        draw.text(contact_pos, data['contact_info'], font=font_contact, fill=(255, 255, 255, 200))
        
        current_y = header_height + 150
        item_padding = 250
        text_color = secondary_color if (secondary_color[0] + secondary_color[1] + secondary_color[2] < 384) else (20,20,20)

        for item in data['menu_items']:
            item_name_bbox = font_item.getbbox(item['name'])
            draw.text((item_padding, current_y), item['name'], font=font_item, fill=text_color)
            
            price_bbox = font_price.getbbox(item['price'])
            price_width = price_bbox[2] - price_bbox[0]
            draw.text((A4_WIDTH - item_padding - price_width, current_y), item['price'], font=font_price, fill=text_color)
            
            line_y = current_y + 40
            start_dot = item_padding + item_name_bbox[2] + 30
            end_dot = A4_WIDTH - item_padding - price_width - 30
            for x in range(start_dot, end_dot, 25):
                 draw.ellipse([(x, line_y), (x + 8, line_y + 8)], fill=secondary_color)

            current_y += 120

        filename = f"generated_menu_{int(time.time())}.png"
        filepath = os.path.join("../frontend", filename)
        menu.save(filepath)
        return jsonify({"image_url": filename})

    except Exception as e:
        print(f"Error in menu generation: {e}") 
        return jsonify({"error": f"An unexpected error occurred on the server: {str(e)}"}), 500


# --- ROUTES to SERVE HTML PAGES ---
@app.route('/')
def serve_dashboard():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:filename>')
def serve_page(filename):
    return send_from_directory(app.static_folder, filename)


# --- RUN THE SERVER ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)

