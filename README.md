# Dermatology AI Assistant 🤖

This project is a web application that serves as an AI-powered dermatology assistant. It's built with **FastAPI** and uses the **Groq API** to provide initial skin condition analysis from an image and then engages in an interactive chat to offer more detailed advice.

---

A video walkthrough of the application's core features is available below.

[Watch the Full Demo](demo.mp4)

---

### Features

-   **Image Upload**: Users can upload an image of a skin condition.
-   **Initial Diagnosis**: The application uses a specialized AI model to perform a preliminary clinical analysis of the image.
-   **Interactive Chat**: After the initial analysis, the AI initiates a chat to ask targeted questions and gather more information.
-   **Final Report**: Based on the collected data, the AI provides a comprehensive final report with categorized advice, treatment, warnings, and instructions.
-   **Session Management**: A unique session is created for each user to maintain the chat history and context.

---

### Prerequisites

-   Python 3.8+
-   A **Groq API Key**

---

### Installation

1.  **Clone the repository**:
    ```sh
    git clone <your-repo-url>
    cd <your-repo-folder>
    ```

2.  **Create a virtual environment**:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies**:
    ```sh
    pip install -r requirements.txt
    ```
    *(Note: You'll need to create a `requirements.txt` file from the `pip` imports in the code, or install them manually: `fastapi`, `uvicorn`, `python-dotenv`, `requests`, `Pillow`, `Jinja2`)*

4.  **Set up the environment variable**:
    Create a `.env` file in the project root and add your Groq API key:
    ```
    GROQ_API_KEY="YOUR_GROQ_API_KEY"
    ```

---

### Usage

1.  **Run the application**:
    ```sh
    uvicorn main:app --reload
    ```

2.  **Access the application**:
    Open your web browser and go to `http://127.0.0.1:8000`.

---

### API Endpoints

-   `GET /`: Renders the main HTML page for user interaction.
-   `POST /upload_and_query`: Handles the initial image upload and query, returning the session ID and preliminary analysis.
-   `POST /interactive_chat`: Manages the interactive chat session, taking a session ID and user message.

---

### Project Structure   