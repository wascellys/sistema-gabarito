import cv2
import numpy as np
import pytesseract
from PIL import Image


def validate_sheet_image(image_path):
    """
    Validates if the answer sheet image has sufficient quality for processing.
    
    Returns:
        bool: True if the image is valid, False otherwise
        str: Error message (if any)
    """
    try:
        image = cv2.imread(image_path)
        
        if image is None:
            return False, "Could not load the image"
        
        # Check minimum dimensions
        height, width = image.shape[:2]
        if width < 500 or height < 700:
            return False, "Image is too small. Minimum dimensions: 500x700 pixels"
        
        # Check if image is not too dark or bright
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        
        if mean_brightness < 50:
            return False, "Image is too dark"
        elif mean_brightness > 200:
            return False, "Image is too bright"
        
        return True, "Valid image"
        
    except Exception as e:
        return False, f"Error validating image: {str(e)}"


def process_answer_sheet_image(image_path, num_questions, num_options):
    """
    Processes an answer sheet image and extracts the marked answers.
    
    Args:
        image_path: Path to the answer sheet image
        num_questions: Number of questions on the answer sheet
        num_options: Number of options per question (e.g., 4 for A,B,C,D)
    
    Returns:
        dict: Dictionary with detected answers {'1': 'A', '2': 'C', ...}
        str: Detected sheet code (if possible)
    """
    # Load the image
    image = cv2.imread(image_path)
    
    if image is None:
        raise ValueError("Could not load the image")
    
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply threshold to binarize the image
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    
    # Detect contours (filled circles)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter circular contours (marked bubbles)
    detected_circles = []
    for contour in contours:
        # Calculate area and perimeter
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        # Check if it's approximately circular
        if perimeter > 0:
            circularity = 4 * np.pi * (area / (perimeter * perimeter))
            
            # If circular and has adequate size
            if circularity > 0.7 and 50 < area < 500:
                # Get the center of the circle
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    detected_circles.append((cX, cY, area))
    
    # Sort circles by position (top to bottom, left to right)
    detected_circles.sort(key=lambda x: (x[1], x[0]))
    
    # Group circles by row (question)
    answers = {}
    option_letters = [chr(65 + i) for i in range(num_options)]  # A, B, C, D...
    
    # Simplification: assume circles are organized in rows
    # Each row has num_options circles
    for i in range(0, min(len(detected_circles), num_questions * num_options), num_options):
        question_num = (i // num_options) + 1
        row_circles = detected_circles[i:i+num_options]
        
        # Check which circle is most filled (marked)
        max_fill = 0
        marked_option = None
        
        for idx, (cX, cY, area) in enumerate(row_circles):
            # Extract circle region
            roi = thresh[max(0, cY-10):cY+10, max(0, cX-10):cX+10]
            if roi.size > 0:
                fill = np.sum(roi) / 255
                if fill > max_fill:
                    max_fill = fill
                    marked_option = option_letters[idx] if idx < len(option_letters) else None
        
        if marked_option:
            answers[str(question_num)] = marked_option
    
    # Try to extract the sheet code using OCR
    sheet_code = None
    try:
        # Extract the upper region of the image where the code usually is
        roi_code = gray[0:150, 0:image.shape[1]]
        extracted_text = pytesseract.image_to_string(roi_code)
        
        # Look for "CODE:" or "CÓDIGO:" in the text
        for line in extracted_text.split('\n'):
            if 'CODE' in line.upper() or 'CÓDIGO' in line.upper():
                # Extract the code (assume it's 12 alphanumeric characters)
                parts = line.split(':')
                if len(parts) > 1:
                    sheet_code = parts[1].strip().replace(' ', '')[:12]
                    break
    except Exception as e:
        print(f"Error extracting code: {e}")
    
    return answers, sheet_code


def process_advanced_answer_sheet(image_path, num_questions, num_options):
    """
    Advanced version of answer sheet processing.
    Uses more robust computer vision techniques.
    
    This is a basic implementation that can be improved with:
    - Edge detection and automatic alignment
    - Machine Learning for mark detection
    - Batch processing of multiple answer sheets
    - Image quality validation
    """
    # For now, use the basic function
    return process_answer_sheet_image(image_path, num_questions, num_options)

