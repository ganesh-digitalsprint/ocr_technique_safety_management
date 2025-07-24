
1. **Clone/Create the project structure** following the folder layout shown above.

2. **Install system dependencies:**
   ```bash
   # Windows
   # Download and install Tesseract from: https://github.com/tesseract-ocr/tesseract
   # Download Poppler from: http://blog.alivate.com.au/poppler-windows/
   
   # Ubuntu/Debian
   sudo apt update
   sudo apt install tesseract-ocr tesseract-ocr-hin poppler-utils
   
   # macOS
   brew install tesseract poppler
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup MySQL database:**
   ```sql
   CREATE DATABASE identity_card_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

5. **Configure environment variables** in `.env` file with your specific paths and database credentials.

6. **Run the application:**
   ```bash
   python run.py
   # or
   uvicorn app.main:app --reload
   ```

7. **Access the API:**
   - API Documentation: http://localhost:8000/api/docs
   - Upload endpoint: POST http://localhost:8000/api/v1/identity-cards/upload
