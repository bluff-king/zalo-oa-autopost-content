# Zalo OA Autopost Content

This project automates the process of posting content to Zalo Official Accounts (OA) by extracting information from provided links, generating summaries, adding cover images, and including Call-to-Action (CTA) elements. It streamlines content management for Zalo OA, focusing on efficiency and ease of use.

## Introduction

My solution aims to offer a streamlined content posting experience for Zalo OA. It allows users to quickly process external links, automatically generate engaging content with summaries and relevant visuals, and publish them with integrated CTAs, simplifying the content management workflow.

## DEMO
<!-- ![Demo Image](p_ai_change.png)
Visualize Change by Dictionary and AI-Mistral

![Demo Image](p_image.png)
Final look on private website -->

## Requirements

To run this project, you will need:
- Python 3.x
- Required Python libraries. A `requirements.txt` file will be provided for easy installation.

## Infer

To set up and run the project, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/bluff-king/zalo-oa-autopost-content.git
    ```

2.  **Navigate to the project directory:**
    ```bash
    cd zalo-oa-autopost-content
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your API key:**
    Create a file named `key.env` in the project root and add your OpenRouter API key:
    ```
    GEMINI_API_KEY=your_gemini_api_key_here
    ```
    Replace `your_gemini_api_key_here` with your actual API key.

5.  **Run the Zalo OA Autopost pipeline:**
    ```bash
    python3 CTA_post_main.py
    ```
    This script will continuously run the posting pipeline, cleaning up temporary files and then processing new links.
5.  **You can add link to links.json by api:**
    Open postman, fill http://127.0.0.1:5467/add-link, change method to POST, go to body, form-data, create new <key>: <link>, and in the value collumn, attach the link you want.
## License

This project is licensed under the MIT License - see the LICENSE file for details.
