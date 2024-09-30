# Cloud Media Thumbnail Generator

## Overview
Cloud Media Thumbnail Generator is a Flask-based web application that creates thumbnails for media files (images and videos) hosted in Google Cloud Storage. It downloads files from cloud storage, processes them to generate thumbnails, and re-uploads them for public access.

## Features
- **Supports multiple media types**: Generates thumbnails for images (JPEG, PNG, WebP, etc.) and videos (MP4, AVI, MOV, etc.).
- **Google Cloud Integration**: Downloads and uploads files to Google Cloud Storage.
- **REST API**: Provides an endpoint to trigger thumbnail generation and check server status.

## Prerequisites
- **Python 3.8+**
- **Google Cloud SDK**: To interact with Google Cloud Storage.
- **FFmpeg**: Required for video processing.
- **ImageMagick**: Utilized via the Wand library for image manipulation.
- **Pillow**: An additional image processing library.

## Installation

1. **Clone the repository**:
    ```sh
    git clone <repository_url>
    cd <repository_name>
    ```

2. **Set up a virtual environment**:
    ```sh
    python3 -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. **Install dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

4. **Configure Google Cloud Credentials**:
   Set the environment variable for Google Cloud credentials:
    ```sh
    export GOOGLE_APPLICATION_CREDENTIALS="credia-696ea-ac31aa925d46.json"
    ```
    Replace `"credia-696ea-ac31aa925d46.json"` with the path to your Google credentials file.

## Usage

1. **Start the server**:
    ```sh
    python app.py
    ```
    The app will run on `http://0.0.0.0:5000` by default.

2. **API Endpoints**:

   - **Generate Thumbnails** (`POST /thumbnail`):
     - **Payload**: JSON containing a list of `file_urls` to media files in Google Cloud Storage.
     - **Example Request**:
       ```json
       {
         "file_urls": [
           "gs://bucket-name/path/to/image.jpg",
           "gs://bucket-name/path/to/video.mp4"
         ]
       }
       ```
     - **Response**: Returns URLs for the generated thumbnails.

   - **Server Status** (`GET /ping`):
     - Checks if the server is running.
     - **Example Response**:
       ```json
       {
         "message": "App running"
       }
       ```

## Technologies Used
- **Flask**: Backend framework to expose the APIs.
- **Google Cloud Storage**: For storing media files and thumbnails.
- **FFmpeg**: Video processing tool.
- **Wand** (ImageMagick wrapper) and **Pillow**: For image manipulation.

## Running in Production
To run the application in a production environment, use a WSGI server like **Gunicorn**:
```sh
gunicorn -w 4 -b 0.0.0.0:5000 app:app
