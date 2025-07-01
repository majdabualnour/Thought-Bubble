import cv2
import numpy as np
# from rembg import remove
import mediapipe as mp

# Initialize MediaPipe Selfie Segmentation
mp_selfie_segmentation = mp.solutions.selfie_segmentation
selfie_segmentation = mp_selfie_segmentation.SelfieSegmentation(model_selection=1)

def remove_background(image):
    # Convert to RGB (MediaPipe requires RGB)
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Get segmentation mask
    results = selfie_segmentation.process(rgb_image)
    mask = results.segmentation_mask
    
    # Create binary mask
    condition = np.stack((mask,) * 3, axis=-1) > 0.1
    bg_removed = np.where(condition, rgb_image, 0)
    
    # Convert back to BGR for OpenCV
    bg_removed = cv2.cvtColor(bg_removed.astype(np.uint8), cv2.COLOR_RGB2BGR)
    
    return bg_removed

def advanced_cartoon_effect(image):
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply edge-preserving smoothing
    smooth = cv2.edgePreservingFilter(image, flags=1, sigma_s=60, sigma_r=0.4)
    
    # Get edges using adaptive threshold
    gray = cv2.medianBlur(gray, 9)
    edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                cv2.THRESH_BINARY, 9, 9)
    
    # Combine edges with smoothed image
    edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    cartoon = cv2.bitwise_and(smooth, edges_colored)
    
    # Enhance colors
    cartoon = cv2.detailEnhance(cartoon, sigma_s=10, sigma_r=0.15)
    
    return cartoon

def apply_custom_background(cartoon, bg_path=None):
    if bg_path:
        bg = cv2.imread(bg_path)
        bg = cv2.resize(bg, (cartoon.shape[1], cartoon.shape[0]))
    else:
        # Create a gradient background if none provided
        bg = np.zeros_like(cartoon)
        for i in range(3):
            bg[:,:,i] = np.linspace(50, 200, bg.shape[1])
    
    # Combine with cartoon (where cartoon isn't black)
    mask = cv2.cvtColor(cv2.threshold(cartoon, 1, 255, cv2.THRESH_BINARY)[1], cv2.COLOR_BGR2GRAY)
    result = np.where(mask[:,:,np.newaxis], cartoon, bg)
    
    return result.astype(np.uint8)

# Initialize webcam
cap = cv2.VideoCapture(0)
saved = False

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Flip frame horizontally for mirror effect
    frame = cv2.flip(frame, 1)
    
    # Remove background
    bg_removed = remove_background(frame)
    
    # Apply cartoon effect
    cartoon = advanced_cartoon_effect(bg_removed)
    
    # Apply custom background
    final_output = apply_custom_background(cartoon)
    
    # Display
    cv2.imshow('Cartoon Avatar', final_output)
    
    # Key controls
    key = cv2.waitKey(1)
    if key == ord('q'):
        break
    elif key == ord('s'):
        cv2.imwrite('cartoon_avatar.png', final_output)
        print("Avatar saved as cartoon_avatar.png")
        saved = True

cap.release()
cv2.destroyAllWindows()

if saved:
    print("Your cartoon avatar has been saved successfully!")